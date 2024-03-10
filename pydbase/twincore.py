#!/usr/bin/env python3

'''!
    @mainpage

        Database with two files. One for data, one for index;

        The reason for the 'twin' name is that two files are created.
        The first contains the data, the second contains the
        offsets (indexes) and hashes.

        The second file can be re-built easily from the first
        using the reindex option.

        Structure of the data:

            32 byte header, starating with FILESIG;

            4 bytes    4 bytes          4 bytes         Variable
            ------------------------------------------------------------
            RECSIG     Hash_of_key      Len_of_key      DATA_for_key
            RECSEP     Hash_of_payload  Len_of_payload  DATA_for_payload
                .
                .

            RECSIG     Hash_of_key      Len_of_key      DATA_for_key
            RECSEP     Hash_of_payload  Len_of_payload  DATA_for_payload

        Deleted records are marked with RECSIG mutated from RECB to RECX

        New data is appended to the end, no duplicate filtering is done.
        Retrieval is searched from reverse, the latest record with this key
        is retrieved first.

        Verbosity:    (use the '-v' option multiple times)

            0 =  no output
            1 =  normal, some items printed, short record ;
            2 =  more detail; full record (-vv)
            3 =  more detail + damaged records (-vvv)

        Debug:    (use the '-d' option with number)

            0 =  no output
            1 =  normal, some items
            2 =  more details

        History:

            1.1         Tue 20.Feb.2024     Initial release
            1.2.0       Mon 26.Feb.2024     Moved pip home to pydbase/
            1.4.0       Tue 27.Feb.2024     Addedd pgdebug
            1.4.2       Wed 28.Feb.2024     Fixed multiple instances
            1.4.3       Wed 28.Feb.2024     ChainAdm added
            1.4.4       Fri 01.Mar.2024     Tests for chain functions
            1.4.5       Fri 01.Mar.2024     Misc fixes
            1.4.6       Mon 04.Mar.2024     Vacuum count on vacuumed records
            1.4.7       Tue 05.Mar.2024     In place record update
            1.4.8       Sat 09.Mar.2024     Added new locking mechanism

'''

import  os, sys, getopt, signal, select, socket, time, struct
import  random, stat, os.path, datetime, threading
import  struct, io

base = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(base, '..', 'pydbase'))

from twinbase import *

Version = "1.4.8"

# ------------------------------------------------------------------------

class TwinCore(TwinCoreBase):

    '''

     Data file and index file; protected by locks
     The TWIN refers to separate files for data / index.

    '''

    def __init__(self, fname = "pydbase.pydb", pgdebug = 0, devmode = 1):

        self.cnt = 0
        self.fname = fname
        self.lckname  = os.path.splitext(self.fname)[0] + ".lock"
        self.idxname  = os.path.splitext(self.fname)[0] + ".pidx"
        self.pgdebug = pgdebug
        self.base_verbose  = 0
        self.devmode = devmode
        self.lock = FileLock(self.lckname)

        # Make sure only one process can use this
        self.lock.waitlock() #self.lckname)

        super(TwinCore, self).__init__(pgdebug)

        #print("initializing core with", fname, pgdebug)
        #self.pool = threading.BoundedSemaphore(value=1)

        # It was informative at one point
        if self.pgdebug > 4:
            pass
            #print("fname:    ", fname)
            #print("idxname:  ", self.idxname)
            #print("lockname: ", self.lckname)

        self.lasterr = "No Error"

        #print("Q pid", os.getpid())

        #print("pid", os.getpid())
        # Initial file creation
        # Nuke false index
        try:
            if not os.path.isfile(self.fname):
                #os.rename(self.idxname, self.idxname + ".old")
                os.remove(self.idxname)
        except:
            pass

        self.fp = self.softcreate(self.fname)
        self.ifp = self.softcreate(self.idxname)

        buffsize = self.getsize(self.fp)
        if buffsize < HEADSIZE:
            #print("initial padding")
            self.create_data(self.fp)
            #try:
            #    # There was no file, delete index, if any
            #    os.rename(self.idxname, self.idxname + ".dangle")
            #    #os.remove(self.idxname)
            #except:
            #    pass

            #print("initial padding")
            self.create_idx(self.ifp)
        else:
            # Initial index creation
            #self.ifp = self.softcreate(self.idxname)
            indexsize = self.getsize(self.ifp)

            # See if valid index
            if indexsize < HEADSIZE:
                self.create_idx(self.ifp)
                # It was an existing data, new index needed
                if self.base_verbose > 0:
                        print("Reindexing")
                self.__reindex()

        # Check
        if  self.getbuffstr(0, 4) != FILESIG:
            print("Invalid data signature")
            self.lock.unlock()  #dellock(self.lckname)
            raise  RuntimeError("Invalid database signature.")

        #print("buffsize", buffsize, "indexsize", indexsize)
        self.lock.unlock() #dellock(self.lckname)

    def version(self):
        ''' Return version sting. '''
        return Version

    def flush(self):

        ''' Flush files to disk. '''

        if self.pgdebug > 9:
            print("Flushing", self.fp, self.ifp)

        try:
            if hasattr(self, "fp"):
                if self.fp:
                    self.fp.flush()
            if hasattr(self, "ifp"):
                if self.ifp:
                    self.ifp.flush()
        except:
            print("Cannot flush files", sys.exc_info())

    def getdbsize(self):

        ''' Return the DB size in records. This includes ALL records, including
        deleted and damaged. This number can be used to iterate all records
        in the database. Usually from end to beginning. '''

        ret = self._getdbsize(self.ifp)
        if not ret:
            ret = 0
        return ret

    def _getdbsize(self, ifp):

        ''' Return number of records. Return total including deleted / damaged. '''

        try:
            #chash = self.getidxint(CURROFFS) - HEADSIZE
            chash = self.getsize(ifp) - HEADSIZE
            ret = int(chash / (2 * self.INTSIZE))
        except:
            ret = 0

        return  ret

    # --------------------------------------------------------------------
    def _rec2arr(self, rec):

        arr = []
        sig = self.getbuffstr(rec, self.INTSIZE)

        if sig == RECDEL:
            return arr

        if sig != RECSIG:
            if self.base_verbose > 0:
                print(" Damaged data (sig) '%s' at" % sig, rec)
            return arr

        hash = self.getbuffint(rec+4)
        blen = self.getbuffint(rec+8)
        data = self.getbuffstr(rec + 12, blen)

        if base_integrity:
            ccc = self.hash32(data)
            if self.base_verbose > 1:
                print("rec", rec, "hash", hex(hash), "check", hex(ccc))
            if hash != ccc:
                if self.base_verbose > 0:
                    print("Error on hash at rec", rec, "hash", hex(hash), "check", hex(ccc))
                return []

        #print("%5d pos %5d" % (cnt, rec), "hash %8x" % hash, "ok", ok, "len=", blen, end=" ")

        endd = self.getbuffstr(rec + 12 + blen, self.INTSIZE)
        if endd != RECSEP:
            if self.base_verbose > 0:
                print(" Damaged data (sep) '%s' at" % endd, rec)
            return arr

        rec2 = rec + 16 + blen;
        hash2 = self.getbuffint(rec2)
        blen2 = self.getbuffint(rec2+4)
        data2 = self.getbuffstr(rec2+8, blen2)

        if base_integrity:
            ccc2 = self.hash32(data2)
            if self.base_verbose > 1:
                print("rec", rec, "hash2", hex(hash2), "check2", hex(ccc2))
            if hash2 != ccc2:
                if self.base_verbose > 0:
                    print("Error on hash at rec", rec, "hash2", hex(hash2), "check2", hex(ccc2))
                return []

        arr = [data, data2]
        return arr

    # -------------------------------------------------------------------
    # Originator, dump single record

    def  dump_rec(self, rec, cnt):

        ''' Print record to the screen. '''

        if self.pgdebug > 1:
            print("Dump Rec at", rec)

        cnt2 = 0
        sig = self.getbuffstr(rec, self.INTSIZE)
        if self.pgdebug > 5:
            print("Sig ", sig, "at", rec)

        if sig == RECDEL:
            if base_showdel:
                klen = self.getbuffint(rec+8)
                kdata = self.getbuffstr(rec+12, klen)
                rec2 = rec + 16 + klen;
                blen = self.getbuffint(rec2+4)
                data = self.getbuffstr(rec2+8, blen)

                print(" Del at", rec, "key:", kdata, "data:", truncs(data))
            return cnt2

        if sig != RECSIG:
            if self.base_verbose > 1:
                print(" Damaged data (sig) '%s' at" % sig, rec)
            return cnt2

        hash = self.getbuffint(rec+4)
        blen = self.getbuffint(rec+8)

        if blen < 0:
            print("Invalid key length %d at %d" % (blen, rec))
            return cnt2

        data = self.getbuffstr(rec+12, blen)
        if base_integrity:
            ccc = self.hash32(data)
            if self.base_verbose > 1:
                print("rec", rec, "hash", hex(hash), "check", hex(ccc))
            if hash != ccc:
                if self.base_verbose > 0:
                    print("Error on hash at rec", rec, "hash", hex(hash), "check", hex(ccc))
                return []

        endd = self.getbuffstr(rec + 12 + blen, self.INTSIZE)
        if endd != RECSEP:
            if self.base_verbose > 0:
                print(" Damaged data (sep) '%s' at" % endd, rec)
            return cnt2

        rec2 = rec + 16 + blen;
        hash2 = self.getbuffint(rec2)
        blen2 = self.getbuffint(rec2+4)

        if blen2 < 0:
            print("Invalid data length %d at %d" % (blen2, rec))
            return cnt2

        data2 = self.getbuffstr(rec2+8, blen2)
        if base_integrity:
            ccc2 = self.hash32(data2)
            if self.base_verbose > 1:
                print("rec", rec, "hash2", hex(hash), "check2", hex(ccc))
            if hash2 != ccc2:
                if self.base_verbose > 0:
                    print("Error on hash at rec", rec, "hash2", hex(hash), "check2", hex(ccc))
                return []

        if self.base_verbose > 2:
            print("%-5d pos %5d" % (cnt, rec), "%8x" % hash, "len", blen, data,
                                                        "%8x" % hash2,"len", blen2, data2)

        elif self.base_verbose > 1:
            print("%-5d pos %5d" % (cnt, rec), "%8x" % hash, "len", blen, data,
                                                        "%8x" % hash2,"len", blen2, data2)
        elif self.base_verbose:
            print("%-5d pos %5d" % (cnt, rec),  data, data2)
        else:
            print("%-5d pos %5d" % (cnt, rec), "Data:", truncs(data, 18), "Data2:", truncs(data2, 18))

        cnt2 += 1
        return cnt2

    def  check_rec(self, rec, cnt2):

        ''' Check record. Verbose to the screen. Return number of errors.'''

        ret = 0
        sig = self.getbuffstr(rec, self.INTSIZE)

        # Do not check deleted, say OK
        if sig == RECDEL:
            if self.base_verbose > 1:
                print(" Deleted data '%s' at %d (%d)" % (sig, rec, cnt2))
            ret = 1
            return ret

        if sig != RECSIG:
            if self.base_verbose > 0:
                print(" Damaged data (sig) '%s' at %d (%d)" % (sig, rec, cnt2))
            #if self.base_verbose > 1:
            #    print("Data", data)

            return ret

        hash = self.getbuffint(rec+4)
        blen = self.getbuffint(rec+8)

        if blen <= 0:
            if self.base_verbose > 1:
                print("Invalid key length %d at %d" % (blen, rec))
            return ret

        data = self.getbuffstr(rec+12, blen)
        ccc = self.hash32(data)
        if hash != ccc:
            if self.base_verbose > 1:
                print("Data", data)
            elif self.base_verbose > 0:
                print("Error on hash at rec", rec, cnt2, "hash",
                                            hex(hash), "check", hex(ccc))

            return ret

        endd = self.getbuffstr(rec + 12 + blen, self.INTSIZE)
        if endd != RECSEP:
            if self.base_verbose > 0:
                print(" Damaged data (sep) '%s' at %d %d %d" % (endd, rec, cnt2))
            return ret

        rec2 = rec + 16 + blen;
        hash2 = self.getbuffint(rec2)
        blen2 = self.getbuffint(rec2+4)

        if blen2 < 0:
            if self.base_verbose > 1:
                print("Invalid data length2 %d at %d" % (blen2, rec))
            return ret

        data2 = self.getbuffstr(rec2+8, blen2)
        ccc2 = self.hash32(data2)
        if hash2 != ccc2:
            if self.base_verbose > 1:
                print("Data", data, "Data2", data2)
            elif self.base_verbose > 0:
                print("Error on hash2 at rec", rec, cnt2, "hash2",
                                        hex(hash2), "check2", hex(ccc2))

            return ret

        if self.base_verbose > 2:
            print("Record at %d (%d) OK." % (rec, cnt2))

        ret += 1
        return ret

    # --------------------------------------------------------------------
    # Internal; no locking

    def  __dump_data(self, lim = INT_MAX, skip = 0, dirx = 0):

        ''' Put all data to screen worker function. '''

        #if self.pgdebug:
        #    print("dump_data()", "lim =", hex(lim), "skip=", skip, "dirx =", dirx)


        cnt = skip; cnt2 = 0
        curr =  chash = HEADSIZE  + self._getdbsize(self.ifp) * self.INTSIZE * 2

        # Direction sensitivity
        if dirx:
            rrr = range(HEADSIZE + skip * self.INTSIZE * 2, chash, self.INTSIZE * 2)
        else:
            rrr = range(chash - self.INTSIZE * 2, HEADSIZE  - self.INTSIZE * 2, -self.INTSIZE * 2)

        for aa in rrr:
            rec = self.getidxint(aa)

            #print(aa, rec)
            if not base_quiet:
                cnt2 += 1
                ret = self.dump_rec(rec, cnt)

                if not ret:
                    if self.pgdebug > 5:
                        print("Deleted / empty record at", cnt)

                if ret:
                    cnt += 1
                    if cnt >= lim:
                        break

    def  dump_data(self, lim = INT_MAX, skip = 0):

        ''' Put all data to screen. '''

        self.__dump_data(lim, skip, 1)

    def  revdump_data(self, lim, skip = 0):

        ''' Put all data to screen in reverse order. '''

        self.__dump_data(lim, skip)

    def  reindex(self):

        ''' Re create index file. '''

        self.lock.waitlock() #self.lckname)
        ret = self.__reindex()
        self.lock.unlock    #dellock(self.lckname)
        return ret

    # --------------------------------------------------------------------

    def  __reindex(self):

        ''' Recover index. Make sure the DB in not in session.  '''

        ret = 0

        #curr = self.getbuffint(CURROFFS) - HEADSIZE
        curr =  self._getdbsize(self.ifp) * self.INTSIZE * 2

        reidx = os.path.splitext(self.fname)[0]  + "_tmp_" + ".pidx"
        tempifp = self.softcreate(reidx)
        self.create_idx(tempifp)
        dlen = self.getsize(self.fp)

        if self.base_verbose > 2:
           print("curr", curr, "dlen", dlen)

        aa =  HEADSIZE
        while 1:
            if aa >= dlen:
                break

            sig = self.getbuffstr(aa, self.INTSIZE)
            # Check if sig is correct
            if sig != RECSIG:
                print("Invalid sig .. resync needed")
                raise

            #print("reind", aa)

            try:
                hhh2 = self.getbuffint(aa + 4)
                lenx = self.getbuffint(aa + 8)
                if lenx < 0:
                    print("Invalid key length")
                sep =  self.getbuffstr(aa + 12 + lenx, self.INTSIZE)
                len2 =  self.getbuffint(aa + 20 + lenx)
                if len2 < 0:
                    print("Invalid record length")
            except:
                print("in reindex", sys.exc_info())

            if self.base_verbose == 1:
                print(aa, "sig", sig, "hhh2", hex(hhh2), "len", lenx, \
                    "sep", sep, "len2", len2)
            if self.base_verbose > 1:
                data =  self.getbuffstr(aa + 12, lenx)
                data2 =  self.getbuffstr(aa + 24 + lenx, len2)
                print(aa, "sig", sig, "data", data, "data2", data2)

            # Update / Append index
            #hashpos = self._getint(tempifp, CURROFFS)
            hashpos =  HEADSIZE  + self._getdbsize(tempifp) * self.INTSIZE * 2

            self._putint(tempifp, hashpos, aa)
            self._putint(tempifp, hashpos + self.INTSIZE, hhh2)

            # This is a shame .. did not flush to file immidiately
            tempifp.flush()

            #self._putint(tempifp, hashpos, self.fp.tell())

            # This is dependent on the database structure
            aa += lenx + len2 + 24
            ret += 1

        # Make it go out of scope
        self.fp.flush()
        self.ifp.flush();
        self.ifp.close()
        tempifp.flush();
        tempifp.close()

        # Now move files
        try:
            os.remove(self.idxname)
        except:
            pass

        #print("rename", reidx, "->", self.idxname)
        os.rename(reidx, self.idxname)

        # Activate new index
        self.ifp = self.softcreate(self.idxname)
        return ret

    def __save_error(self, rec, vacerrfp):

        vacerrfp.write(b"Err at %8d\n" % rec)

        try:
            ddd = self.getbuffstr(rec, 100)
        except:
            pass

        # Find next valid record, print up to that
        found = 0
        for aa in range(len(ddd)):
            if ddd[aa:aa+4] == RECSIG:
                found = True
                #print("found:", ddd[:aa+4])
                vacerrfp.write(ddd[:aa])
                break
        if not found:
            vacerrfp.write(ddd)

    # ----------------------------------------------------------------

    def  vacuum(self):

        '''
            Remove all deleted data. Reindex.
            The db is locked while the vacuum is in operation, but
            make sure the DB in not in session, and no pending
            operations are present (like find / retrieve cycle).
        '''

        self.lock.waitlock() #self.lckname)
        ret = self._vacuum()
        self.lock.unlock()  #dellock(self.lckname)
        return ret

    def  _vacuum(self):

        vacname = os.path.splitext(self.fname)[0] + "_vac_" + ".pydb"
        vacerr  = os.path.splitext(self.fname)[0] +  ".perr"
        vacidx = os.path.splitext(vacname)[0]  + ".pidx"

        if self.pgdebug > 4:
            print("vacname", vacname)
            print("vacidx", vacidx)
            print("vacerr", vacerr)

        ret = 0; vac = 0

        # Open for append
        vacerrfp = self.softcreate(vacerr, False)
        vacerrfp.seek(0, os.SEEK_END)

        try:
            # Make sure they are empty
            os.remove(vacname)
            os.remove(vacidx)
        except:
            pass

        # It is used to raise the scope so vacuumed DB closes
        if 1:
            vacdb = TwinCore(vacname)
            vacdb.lock.waitlock()

            skip = 0; cnt = 0
            chash =  self._getdbsize(self.ifp) * self.INTSIZE * 2
            rrr = range(HEADSIZE + skip * self.INTSIZE * 2, chash + HEADSIZE, self.INTSIZE * 2)
            for aa in rrr:
                rec = self.getidxint(aa)
                sig = self.getbuffstr(rec, self.INTSIZE)
                if sig == RECDEL:
                    ret += 1
                    vac += 1
                    if self.pgdebug > 1:
                        print("deleted", rec)
                elif sig != RECSIG:
                    if self.base_verbose:
                        print("Detected error at %d" % rec)
                    ret += 1
                    self.__save_error(rec, vacerrfp)
                else:
                    global base_integrity
                    tmpi = base_integrity
                    base_integrity = True
                    arr = self.get_rec_offs(rec)
                    base_integrity = tmpi

                    if self.pgdebug > 1:
                        print(cnt, "vac rec", rec, arr)

                    if len(arr) > 1:
                        hhh2 = self.hash32(arr[0])
                        hhh3 = self.hash32(arr[1])
                        vacdb.__save_data(hhh2, arr[0], hhh3, arr[1])
                        #vac += 1
                    else:
                        # This could be from empty bacause of hash error
                        self.__save_error(rec, vacerrfp)
                        if self.pgdebug > 0:
                            print("Error on vac: %d" % rec)
                cnt += 1

            vacdb.lock.unlock()  #dellock(vacdb.lckname)

            # if vacerr is empty
            try:
                if os.stat(vacerr).st_size == 0:
                    #print("Vac error empty")
                    os.remove(vacerr)
            except:
                print("vacerr", sys.exc_info())

        self.lock.unlock()  #dellock(self.lckname)

        # Any vacummed?
        if vac > 0:
            # Make it go out of scope
            self.fp.flush(); self.ifp.flush()
            self.fp.close(); self.ifp.close()

            # Now move files
            try:
                os.remove(self.fname);  os.remove(self.idxname)
            except:
                pass

            if self.pgdebug > 1:
                print("rename", vacname, "->", self.fname)
                print("rename", vacidx, "->", self.idxname)

            os.rename(vacname, self.fname)
            os.rename(vacidx, self.idxname)

            self.lock.waitlock() #self.lckname)
            self.fp = self.softcreate(self.fname)
            self.ifp = self.softcreate(self.idxname)
            self.lock.unlock()  #dellock(self.lckname)

        else:
            # Just remove non vacuumed files
            if self.pgdebug > 1:
                print("deleted", vacname, vacidx)
            try:
                os.remove(vacname)
                os.remove(vacidx)
            except:
                pass

        #print("ended vacuum")
        return ret, vac

    def  get_rec(self, recnum):

        ''' Get record from database; recnum is a zero based record counter. '''

        if self.pgdebug:
            print("getrec()", recnum)

        rsize = self._getdbsize(self.ifp)
        if recnum >= rsize:
            #print("Past end of data.");
            raise  RuntimeError( \
                    "Past end of Data. Asking for %d while max is 0 .. %d records." \
                                     % (recnum, rsize-1) )
            return []

        chash = self.getidxint(CURROFFS)
        #print("chash", chash)
        offs = self.getidxint(HEADSIZE + recnum * self.INTSIZE * 2)

        #print("offs", offs)
        return self._rec2arr(offs)

    def  get_rec_offs(self, recoffs):

        ''' Return record by offset. '''

        rsize = self.getsize(self.fp)
        if recoffs >= rsize:
            #print("Past end of data.");
            raise  RuntimeError( \
                    "Past end of File. Asking for offset %d file size is %d." \
                                     % (recoffs, rsize) )
            return []

        sig = self.getbuffstr(recoffs, self.INTSIZE)
        if sig == RECDEL:
            if self.base_verbose:
                print("Deleted record.")
            return []
        if sig != RECSIG:
            print("Unlikely offset %d is not at record boundary." % recoffs, sig)
            return []
        #print("recoffs", recoffs)
        return self._rec2arr(recoffs)

    def  get_key_offs(self, recoffs):

        ''' Get key by offset. '''

        rsize = self.getsize(self.fp)
        if recoffs >= rsize:
            #print("Past end of data.");
            raise  RuntimeError( \
                    "Past end of File. Asking for offset %d file size is %d." \
                                     % (recoffs, rsize) )
            return []

        sig = self.getbuffstr(recoffs, self.INTSIZE)
        if sig == RECDEL:
            if self.base_verbose:
                print("Deleted record.")
            return []
        if sig != RECSIG:
            print("Unlikely offset %d is not at record boundary." % recoffs, sig)
            return []
        #print("recoffs", recoffs)
        return self._rec2arr(recoffs)[0]

    def  del_rec(self, recnum):

        ''' Delete by record number.
            Deleted record is marked as deleted but not removed.
            Deleted records are ignored in further operations.
            Use 'vacuum' to actually remove record.
        '''

        rsize = self._getdbsize(self.ifp)
        if recnum >= rsize:
            if self.base_verbose:
                print("Past end of data.");
            return False
        chash = self.getidxint(CURROFFS)
        #print("chash", chash)
        offs = self.getidxint(HEADSIZE + recnum * self.INTSIZE * 2)
        #print("offs", offs)
        old = self.getbuffstr(offs, self.INTSIZE)
        if old == RECDEL:
            if self.base_verbose:
                print("Record at %d already deleted." % offs);
            return False

        self.putbuffstr(offs, RECDEL)
        return True

    def  del_rec_offs(self, recoffs):

        ''' Delete record by file offset. '''

        rsize = self.getsize(self.fp)
        if recoffs >= rsize:
            #print("Past end of data.");
            raise  RuntimeError( \
                    "Past end of File. Asking for offset %d file size is %d." \
                                     % (recoffs, rsize) )
            return False

        sig = self.getbuffstr(recoffs, self.INTSIZE)
        if sig != RECSIG  and sig != RECDEL:
            print("Unlikely offset %d is not at record boundary." % recoffs, sig)
            return False

        self.putbuffstr(recoffs, RECDEL)
        return True

    # Check integrity

    def integrity_check(self, skip = 0, count = 0xffffffff):

        ''' Check record integrity for 'count' records.
            Skip number of records.
        '''

        self.lock.waitlock()    #(self.lckname)
        ret = 0; cnt2 = 0; cnt3 = 0;
        #chash = self.getidxint(CURROFFS)        #;print("chash", chash)
        chash =  HEADSIZE  + self._getdbsize(self.ifp) * self.INTSIZE * 2
        # Direction sensitivity
        rrr = range(HEADSIZE + skip * self.INTSIZE * 2, chash, self.INTSIZE * 2)
        for aa in rrr:
            rec = self.getidxint(aa)
            #print(aa, rec)
            ret += self.check_rec(rec, cnt2)
            cnt2 += 1
            cnt3 += 1
            if cnt3 >= count:
                break
        self.lock.unlock() #dellock(self.lckname)
        return ret, cnt2

    def  retrieve(self, strx, limx = 1):

        ''' Retrive in reverse, limit it. '''

        if type(strx) != type(b""):
            strx = strx.encode(errors='strict')

        hhhh = self.hash32(strx)
        if self.pgdebug > 2:
            print("strx", strx, hhhh)

        #chash = self.getidxint(CURROFFS)
        chash =  HEADSIZE  + self._getdbsize(self.ifp) * self.INTSIZE * 2

        #;print("chash", chash)
        arr = []

        self.lock.waitlock() #(self.lckname)

        #for aa in range(HEADSIZE + self.INTSIZE * 2, chash, self.INTSIZE * 2):
        for aa in range(chash - self.INTSIZE * 2, HEADSIZE  - self.INTSIZE * 2, -self.INTSIZE * 2):
            rec = self.getidxint(aa)
            sig = self.getbuffstr(rec, self.INTSIZE)
            if sig == RECDEL:
                if self.base_verbose > 3:
                    print(" Deleted record '%s' at" % sig, rec)
            elif sig != RECSIG:
                if self.base_verbose:
                    print(" Damaged data '%s' at" % sig, rec)
            else:
                hhh = self.getbuffint(rec+4)
                if hhh == hhhh:
                    arr.append(self.get_rec_offs(rec))
                    if len(arr) >= limx:
                        break
        self.lock.unlock()  #dellock(self.lckname)

        return arr

    # Return record offset

    def  _recoffset(self, strx, limx = INT_MAX, skipx = 0):

        #chash = self.getidxint(CURROFFS)            #;print("chash", chash)
        chash =  HEADSIZE  + self._getdbsize(self.ifp) * self.INTSIZE * 2
        rec = 0; blen = 0; data = ""
        arr = []
        if type(strx) != type(b""):
            strx2 = strx.encode(errors='strict');
        else:
            strx2 = strx

        #print("_recoffset", strx2)

        #for aa in range(HEADSIZE + self.INTSIZE * 2, chash, self.INTSIZE * 2):
        for aa in range(chash - self.INTSIZE * 2, HEADSIZE  - self.INTSIZE * 2, -self.INTSIZE * 2):
            rec = self.getidxint(aa)
            sig = self.getbuffstr(rec, self.INTSIZE)
            if sig == RECDEL:
                if base_showdel:
                    print(" Deleted record '%s' at" % sig, rec)
            elif sig != RECSIG:
                if self.base_verbose > 0:
                    print(" Damaged data '%s' at" % sig, rec)
            else:
                blen = self.getbuffint(rec+8)
                keyz = self.getbuffstr(rec + 12, blen)
                if self.base_verbose > 1:
                    print("_recoffset", keyz)
                if strx2 == keyz:
                    sig = self.getbuffstr(rec + 16 + blen,  self.INTSIZE)
                    xlen = self.getbuffint(rec + 20 + blen)
                    data = self.getbuffstr(rec + 24 + blen, xlen)
                    #print("rec offset", rec + 12,  "key:", keyz, "data:", data)
                    break       # Only the last one
        return rec, rec+24 + blen, len(data)

    def  findrec(self, strx, limx = INT_MAX, skipx = 0):

        ''' Find by string matching substring. '''

        self.lock.waitlock()    #(self.lckname)

        #chash = self.getidxint(CURROFFS)            #;print("chash", chash)
        chash =  HEADSIZE  + self._getdbsize(self.ifp) * self.INTSIZE * 2

        arr = []
        strx2 = strx.encode(errors='strict');

        #print("findrec", strx2)

        #for aa in range(HEADSIZE + self.INTSIZE * 2, chash, self.INTSIZE * 2):
        for aa in range(chash - self.INTSIZE * 2, HEADSIZE  - self.INTSIZE * 2, -self.INTSIZE * 2):
            rec = self.getidxint(aa)
            sig = self.getbuffstr(rec, self.INTSIZE)
            if sig == RECDEL:
                if base_showdel:
                    print(" Deleted record '%s' at" % sig, rec)
            elif sig != RECSIG:
                if self.base_verbose > 0:
                    print(" Damaged data '%s' at" % sig, rec)
            else:
                blen = self.getbuffint(rec+8)
                data = self.getbuffstr(rec + 12, blen)
                if self.base_verbose > 1:
                    print("find", data)
                #if str(strx2) in str(data):
                if strx2 in data:
                    arr.append(self.get_key_offs(rec))
                    #arr.append(rec)

                    if len(arr) >= limx:
                        break
        self.lock.unlock()  #dellock(self.lckname)

        return arr

    def  findrecpos(self, strx, limx = INT_MAX, skipx = 0):

        ''' Find record, return array of positions. '''

        self.lock.waitlock()    #(self.lckname)
        chash =  HEADSIZE  + self._getdbsize(self.ifp) * self.INTSIZE * 2
        arr = []
        if type(strx) != type(b""):
            strx = strx.encode(errors='strict');

        for aa in range(chash - self.INTSIZE * 2, HEADSIZE  - self.INTSIZE * 2, -self.INTSIZE * 2):
            rec = self.getidxint(aa)
            sig = self.getbuffstr(rec, self.INTSIZE)
            if sig == RECDEL:
                if base_showdel:
                    print(" Deleted record '%s' at" % sig, rec)
            elif sig != RECSIG:
                if self.base_verbose > 0:
                    print(" Damaged data '%s' at" % sig, rec)
            else:
                blen = self.getbuffint(rec+8)
                data = self.getbuffstr(rec + 12, blen)
                if self.base_verbose > 1:
                    print("frecpos", data)
                if strx == data:
                    arr.append(rec)
                    if len(arr) >= limx:
                        break

        self.lock.unlock()  #dellock(self.lckname)

        return arr

    def  findrec(self, strx, limx = INT_MAX, skipx = 0):

        ''' Find by string matching substring. '''

        self.lock.waitlock()    #(self.lckname)
        chash =  HEADSIZE  + self._getdbsize(self.ifp) * self.INTSIZE * 2
        arr = []
        if type(strx) != type(b""):
            strx2 = strx.encode(errors='strict');

        #print("findrec", strx2)

        #for aa in range(HEADSIZE + self.INTSIZE * 2, chash, self.INTSIZE * 2):
        for aa in range(chash - self.INTSIZE * 2, HEADSIZE  - self.INTSIZE * 2, -self.INTSIZE * 2):
            rec = self.getidxint(aa)
            sig = self.getbuffstr(rec, self.INTSIZE)
            if sig == RECDEL:
                if base_showdel:
                    print(" Deleted record '%s' at" % sig, rec)
            elif sig != RECSIG:
                if self.base_verbose > 0:
                    print(" Damaged data '%s' at" % sig, rec)
            else:
                blen = self.getbuffint(rec+8)
                data = self.getbuffstr(rec + 12, blen)
                if self.base_verbose > 1:
                    print("find", data)
                #if str(strx2) in str(data):
                if strx2 in data:
                    #arr.append(self.get_key_offs(rec))
                    #arr.append(rec)
                    arr.append(self._rec2arr(rec))
                    if len(arr) >= limx:
                        break
        self.lock.unlock()    #dellock(self.lckname)

        return arr

    # --------------------------------------------------------------------
    # List all active records

    def  listall(self):

        ''' List all active records. Return array id record indexes. '''

        self.lock.waitlock()    #(self.lckname)
        keys = []; arr = []; cnt = 0

        chash =  HEADSIZE  + self._getdbsize(self.ifp) * self.INTSIZE * 2
        maxrec = chash - self.INTSIZE * 2
        rsize = self._getdbsize(self.ifp) - 1

        rrr =  range(maxrec,
                HEADSIZE - self.INTSIZE * 2, -self.INTSIZE * 2)
        for aa in rrr:
            rec = self.getidxint(aa)

            #print(" Scanning at %d %d" % (rec, cnt))

            sig = self.getbuffstr(rec, self.INTSIZE)
            if sig == RECDEL:
                if 1: #base_showdel:
                    print("Deleted record '%s' at" % sig, rec)
            elif sig != RECSIG:
                if 1: #self.base_verbose > 0:
                    print(" Damaged data '%s' at" % sig, rec)
            else:
                    hhh = self.getbuffint(rec+4)
                    print(" Good data '%s' at" % sig, rec, hhh)
                    if hhh not in keys:
                        keys.append(hhh)
                        # as we are going backwards
                        arr.append(rsize - cnt)
                        #print("found", hhh)
            cnt += 1

        keys = []
        self.lock.unlock()  #dellock()self.lckname)

        return arr

    def  find_key(self, keyx, limx = 0xffffffff):

        ''' Find record by key Search from the end, so latest comes first. '''

        self.lock.waitlock()   #self.lckname)

        skip = 0; arr = []; cnt = 0
        try:
            arg2e = keyx.encode()
        except:
            arg2e = keyx

        hhhh = self.hash32(arg2e)
        #print("hashx", "'" + hashx + "'", hex(hhhh), arg2e)

        chash =  HEADSIZE  + self._getdbsize(self.ifp) * self.INTSIZE * 2
        rrr =  range(chash - self.INTSIZE * 2,
                HEADSIZE - self.INTSIZE * 2, -self.INTSIZE * 2)
        for aa in rrr:
            rec = self.getidxint(aa)
            #print(" Scanning at %d %d" % (rec, cnt))

            sig = self.getbuffstr(rec, self.INTSIZE)
            if sig == RECDEL:
                if base_showdel:
                    print("Deleted record '%s' at" % sig, rec)
            elif sig != RECSIG:
                if self.base_verbose > 0:
                    print(" Damaged data '%s' at" % sig, rec)
            else:
                hhh = self.getbuffint(rec+4)
                if hhh == hhhh:
                    if len(arr) >= limx - 1:
                        arr.append(["More data ...",])
                        break
                    arr.append(rec)
                else:
                    pass
                    #print("no match", hex(hhh))

            cnt += 1
        self.lock.unlock()  #dellock()self.lckname)

        return arr


    def  del_data(self, hash, skip = 1):

        ''' Delete data by hash. '''

        cnt = skip
        hhhh = int(hash, 16)                #;print("hash", hash, hhhh)
        curr = self.getbuffint(CURROFFS)    #;print("curr", curr)
        chash = self.getidxint(CURROFFS)    #;print("chash", chash)

        arr = []
        for aa in range(HEADSIZE + skip * self.INTSIZE * 2, chash, self.INTSIZE * 2):
            rec = self.getidxint(aa)

            # Optional check
            #sig = self.getbuffstr(rec, self.INTSIZE)
            #if sig != RECSIG:
            #    print(" Damaged data '%s' at" % sig, rec)

            #blen = self.getbuffint(rec+8)
            #print("data '%s' at" % sig, rec, "blen", blen)

            hhh = self.getbuffint(rec+4)
            if hash == hhh:
                if self.base_verbose > 0:
                    print("Would delete", hhh)

            self.putbuffstr(rec, RECDEL)

            cnt += 1

        return arr

    def  del_rec_bykey(self, strx, maxdelrec = 0xffffffff, skip = 0, dirx = 0):

        ''' Remove record by key. Remove maxdelrec occurances.

                    Input:
                        strx            key to remove
                        maxdelrex       maximum number of records to delete
                        skip            start scanning from offset
                        dirx            False for scanning down, True for up
                    Return:
                        count of records removed

            '''

        if self.pgdebug:
            print("del_rec_bykey()", strx)

        ''' Delete records by key string; needs bin str, converted
            automatically on entry.
        '''

        if type(strx) != type(b""):
            strx = strx.encode()

        if self.base_verbose > 1:
            print("Start delete ", strx, "skip", skip)

        cnt = 0; cnt3 = 0
        #chash = self.getidxint(CURROFFS)    #;print("chash", chash)
        chash =  HEADSIZE  + self._getdbsize(self.ifp) * self.INTSIZE * 2

        # Direction sensitivity
        if dirx:
            rrr = range(HEADSIZE + skip * self.INTSIZE * 2, chash, self.INTSIZE * 2)
        else:
            rrr = range(chash - self.INTSIZE * 2, HEADSIZE  - self.INTSIZE * 2, -self.INTSIZE * 2)

        #for aa in range(HEADSIZE, chash, self.INTSIZE * 2):
        for aa in rrr:
            rec = self.getidxint(aa)
            sig = self.getbuffstr(rec, self.INTSIZE)
            if sig == RECDEL:
                if base_showdel:
                    print(" Deleted record '%s' at" % sig, rec)
            elif sig != RECSIG:
                if self.base_verbose > 0:
                    print(" Damaged data '%s' at" % sig, rec)
            else:
                blen = self.getbuffint(rec+8)
                data = self.getbuffstr(rec + 12, blen)
                if self.base_verbose > 2:
                    print("del iterate recs", cnt3, data, strx)

                if strx == data:
                    if self.base_verbose > 0:
                        print("Deleting", cnt3, aa, data)
                    self.putbuffstr(rec, RECDEL)
                    cnt += 1
                    if cnt >= maxdelrec:
                        break
            cnt3 += 1
        return cnt

    def  save_data(self, header, datax, replace = False):

        ''' Append to the end of file. If replace flag is set, try to overwrite
            in place. If new record is larger, add it as ususal. If smaller,
            the record is padded with spaces. This should not influence most ops.
            (like: int())
            This feature allows the database update wthout creating new records.
            Useful for counters or dynamically changing data.

                    Input:
                        header     Header
                        datax      Data

                     Return:
                        The offset of saved data
            '''

        if self.pgdebug > 0:
            print("Save_data()", header, datax)

        self.lock.waitlock()   #self.lckname)
        ret = 0
        was = False
        # Put new data in place
        if replace:
            if type(datax) != type(b""):
                mrep2 = datax.encode()
            else:
                mrep2 = datax

            rrr = self._recoffset(header, 1)
            if rrr[2]:
                #print("Replace rec", hex(rrr[0]), "len:", rrr[1])
                if len(mrep2) <= rrr[2]:
                    #print("Fit")
                    padded = mrep2 + b' ' * (rrr[1] - len(mrep2))
                    #print("Padded", padded)
                    ccc = self.hash32(padded)
                    self.putbuffint(rrr[1] - 8, ccc)
                    #print("ccc", hex(ccc))
                    self.putbuffstr(rrr[1], padded)
                    was = True
                    # This was helpful ... but more systematic approach is needed
                    self.fp.flush()
                    self.ifp.flush()
                    ret =  rrr[0]
        if not was:
            ret = self._save_data2(header, datax)

        self.lock.unlock()  #dellock()self.lckname)

        return ret

    # --------------------------------------------------------------------
    # Save data to database file

    def  _save_data2(self, arg2, arg3):

        # Prepare all args, if cannot encode, use original
        if type(arg2) != type(b""):
            arg2 = arg2.encode()
        if type(arg3) != type(b""):
            arg3 = arg3.encode()

        if self.pgdebug > 1:
            print("args", arg2, "arg3", arg3)

        hhh2 = self.hash32(arg2)
        hhh3 = self.hash32(arg3)

        if self.pgdebug > 1:
            print("_save_data2 hhh2", hhh2, "hhh3", hhh3)

        ret = self.__save_data(hhh2, arg2, hhh3, arg3)

        return ret

    def __save_data(self, hhh2, arg2e, hhh3, arg3e):

        # Update / Append data

        # Building array added some efficiency
        arr = []
        arr.append(RECSIG)
        arr.append(struct.pack("I", hhh2))
        arr.append(struct.pack("I", len(arg2e)))
        arr.append(arg2e)
        arr.append(RECSEP)
        arr.append(struct.pack("I", hhh3))
        arr.append(struct.pack("I", len(arg3e)))
        arr.append(arg3e)
        tmp = b"".join(arr)

        #print(tmp)
        # The pre - assemple to string added 20% efficiency

        #curr = self.getbuffint(CURROFFS)
        curr =  HEADSIZE  + self._getdbsize(self.ifp) * self.INTSIZE * 2
        #print("curr", curr)

        self.fp.seek(0, os.SEEK_END)
        dcurr = self.fp.tell()

        self.fp.write(tmp)

        # This allowed corruption of the data string
        # Update lenght
        #self.putbuffint(CURROFFS, self.fp.tell()) #// - dlink + DATA_LIM)
        #self.fp.seek(curr)
        #print("hashpos", hashpos)

        # Update / Append index
        if self.pgdebug > 1:
            print("__save_data idx", dcurr)

        self.putidxint(curr, dcurr)
        self.putidxint(curr + self.INTSIZE, hhh2)
        #self.putidxint(CURROFFS, self.ifp.tell())

        self.fp.flush()
        self.ifp.flush()

        return curr

    def __del__(self):

        ''' flush file handles and close files. '''

        if hasattr(self, "pgdebug"):
            if self.pgdebug > 9:
                print("__del__ called.")

        #self.flush()

        if hasattr(self, "fp"):
                if self.fp:
                    self.fp.flush()
                    self.fp.close()

        if hasattr(self, "ifp"):
                if self.ifp:
                    self.ifp.flush()
                    self.ifp.close()

# EOF
