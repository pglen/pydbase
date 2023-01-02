#!/usr/bin/env python3

'''!
    @mainpage

    # Twincore

    Database with two files. One for data, one for index;

    The reason for this name is that two files are created. The first contains
    the data, the second contains the offsets (indexes) and hashes.

    The second file can be re-built easily from the first the the reindex option.

    Structure of the data:

        32 byte header, starating with FILESIG;

        4 bytes    4 bytes          4 bytes         Variable
        ------------------------------------------------------------
        RECSIG     Hash_of_key      Len_of_key      DATA_for_key
        RECSEP     Hash_of_payload  Len_of_payload  DATA_for_payload

            .
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

'''

import  os, sys, getopt, signal, select, socket, time, struct
import  random, stat, os.path, datetime, threading
import  struct, io

INT_MAX         = 0xffffffff    # INT_MAX in 'C' py has BIG integer
HEADSIZE        = 32
CURROFFS        = 16
FIRSTHASH       = HEADSIZE
FIRSTDATA       = HEADSIZE
LOCK_TIMEOUT    = 3             # this is in 0.1 sec units

# Accessed from main main file as well

core_quiet      = 0
core_pgdebug    = 0
core_integrity  = 0
core_showdel    = 0
core_lcktimeout = LOCK_TIMEOUT

def trunc(strx, num = 8):
    ''' truncate for printing nicely '''

    # no truncation on high verbose
    #if self.core_verbose > 1:
    #    return strx

    if len(strx) > num:
        strx = strx[:num] + b".."
    return strx


class TwinCoreBase():

    ''' This class provides basis services to twincore. '''

    INTSIZE     = 4

    def __init__(self):

        #print("Initializing core base")

        # Provide placeholders
        self.fp = None
        self.ifp = None
        self.cnt = 0
        self.fname = "" ;        self.idxname = ""
        self.lckname = "";       self.lasterr = ""

    def __del__(self):
        pass
        #print("called __del__", self.fname)

    def getsize(self, buffio):
        pos = buffio.tell()
        endd = buffio.seek(0, io.SEEK_END)
        buffio.seek(pos, io.SEEK_SET)
        return endd

    # --------------------------------------------------------------------
    # Read / write index / data; Data is accessed by int or by str;
    #  Note: data by int is in little endian (intel) order

    def getidxint(self, offs):
        #print("getidxint", offs)
        self.ifp.seek(offs, io.SEEK_SET)
        val = self.ifp.read(4)
        return struct.unpack("I", val)[0]

    def putidxint(self, offs, val):
        #print("putidxint", offs, val)
        pp = struct.pack("I", val)
        self.ifp.seek(offs, io.SEEK_SET)
        self.ifp.write(pp)

    def getbuffint(self, offs):
        self.fp.seek(offs, io.SEEK_SET)
        val = self.fp.read(4)
        return struct.unpack("I", val)[0]

    def putbuffint(self, offs, val):
        #print("putbuffint", offs, val)
        self.fp.seek(offs, io.SEEK_SET)
        cc = struct.pack("I", val)
        self.fp.write(cc)

    def getbuffstr(self, offs, xlen):
        self.fp.seek(offs, io.SEEK_SET)
        val = self.fp.read(xlen)
        return val

    def putbuffstr(self, offs, xstr):
        self.fp.seek(offs, io.SEEK_SET)
        val = self.fp.write(xstr)

    def _putint(self, ifp, offs, val):
        pp = struct.pack("I", val)
        ifp.seek(offs, io.SEEK_SET)
        ifp.write(pp)

    def _getint(self, ifp, offs):
        ifp.seek(offs, io.SEEK_SET)
        val = ifp.read(4)
        return struct.unpack("I", val)[0]

    # Simple file system based locking system
    def waitlock(self):
        cnt = 0
        while True:
            if os.path.isfile(self.lckname):
                #print("waitlock")
                cnt += 1
                time.sleep(0.1)
                # Taking too long; break in
                if cnt > core_lcktimeout:
                    print("Warning: Breaking lock ... ", self.lckname)
                    self.dellock()
                    break
            else:
                fp = self.softcreate(self.lckname)
                # Sun 01.Jan.2023 close it !!!! it is a lock
                fp.close()
                break

    def dellock(self):
        try:
            os.unlink(self.lckname)
        except:
            pass

    # Deliver a 32 bit hash of whatever
    def hash32(self, strx):

        #print("hashing", strx)
        lenx = len(strx);  hashx = int(0)
        for aa in strx:
            hashx +=  int( (aa << 12) + aa)
            hashx &= 0xffffffff
            hashx = int(hashx << 8) + int(hashx >> 8)
            hashx &= 0xffffffff
        return hashx

    def softcreate(self, fname, raisex = True):

        ''' Open for read / write. Create if needed. '''
        fp = None
        try:
            fp = open(fname, "rb+")
        except:
            try:
                fp = open(fname, "wb+")
            except:
                print("Cannot open /create ", fname, sys.exc_info())
                if raisex:
                    raise
        return fp

    # Sub for initial file
    def create_data(self, fp):

        fp.write(bytearray(HEADSIZE))

        fp.seek(0)
        fp.write(TwinCore.FILESIG)
        fp.write(struct.pack("B", 0x03))
        fp.write(struct.pack("I", 0xaabbccdd))
        fp.write(struct.pack("B", 0xaa))
        fp.write(struct.pack("B", 0xbb))
        fp.write(struct.pack("B", 0xcc))
        fp.write(struct.pack("B", 0xdd))
        fp.write(struct.pack("B", 0xff))

        fp.seek(CURROFFS, io.SEEK_SET)
        cc = struct.pack("I", HEADSIZE)
        fp.write(cc)

    def create_idx(self, ifp):

        ifp.write(bytearray(HEADSIZE))

        ifp.seek(0)
        ifp.write(TwinCore.IDXSIG)
        ifp.write(struct.pack("I", 0xaabbccdd))
        ifp.write(struct.pack("B", 0xaa))
        ifp.write(struct.pack("B", 0xbb))
        ifp.write(struct.pack("B", 0xcc))
        ifp.write(struct.pack("B", 0xdd))
        ifp.write(struct.pack("B", 0xff))

        pp = struct.pack("I", HEADSIZE)
        ifp.seek(CURROFFS, io.SEEK_SET)
        ifp.write(pp)


# ------------------------------------------------------------------------

class TwinCore(TwinCoreBase):

    '''

     Data file and index file; protected by locks
     The TWIN refers to separate files for data / index

    '''

    # These are all four bytes, one can read it like integers

    FILESIG     = b"PYDB"
    IDXSIG      = b"PYIX"
    RECSIG      = b"RECB"
    RECDEL      = b"RECX"
    RECSEP      = b"RECS"
    RECEND      = b"RECE"

    def __init__(self, fname = "pydbase.pydb"):

        super(TwinCoreBase, self).__init__()
        #print("initializing core with", fname)

        self.core_verbose  = 0

        self.cnt = 0
        self.fname = fname
        self.idxname = os.path.splitext(self.fname)[0] + ".pidx"
        self.lckname = os.path.splitext(self.fname)[0] + ".lock"
        self.lasterr = "No Error"

        # This will never show ... but it was informative at one point
        if self.core_verbose > 3:
            print("fname", fname, "idxname", self.idxname, "lockname", self.lckname)

        self.waitlock()

        # Initial file creation
        self.fp = self.softcreate(self.fname)
        buffsize = self.getsize(self.fp)
        if buffsize < HEADSIZE:
            #print("initial padding")
            self.create_data(self.fp)
            try:
                # There was no file, delete index, if any
                os.remove(self.idxname)
            except:
                pass
            #print("initial padding")
            self.ifp = self.softcreate(self.idxname)
            self.create_idx(self.ifp)
        else:
            # Initial index creation
            self.ifp = self.softcreate(self.idxname)
            indexsize = self.getsize(self.ifp)

            # See if valid index
            if indexsize < HEADSIZE:
                self.create_idx(self.ifp)
                # It was an existing data, new index needed
                if self.core_verbose > 0:
                    print("Reindexing")
                self.__reindex()

        # Check
        if  self.getbuffstr(0, 4) != TwinCore.FILESIG:
            print("Invalid data signature")
            self.dellock()
            raise  RuntimeError("Invalid database signature.")

        #print("buffsize", buffsize, "indexsize", indexsize)
        self.dellock()

    def getdbsize(self):
        try:
            chash = self.getidxint(CURROFFS) - HEADSIZE
            ret = int(chash / (2 * self.INTSIZE))
        except:
            ret = 0
        return  ret

    # --------------------------------------------------------------------
    def rec2arr(self, rec):

        arr = []
        sig = self.getbuffstr(rec, self.INTSIZE)

        if sig == TwinCore.RECDEL:
            return arr

        if sig != TwinCore.RECSIG:
            print(" Damaged data '%s' at" % sig, rec)
            return arr

        hash = self.getbuffint(rec+4)
        blen = self.getbuffint(rec+8)
        data = self.getbuffstr(rec + 12, blen)

        if core_integrity:
            ccc = self.hash32(data)
            if self.core_verbose > 1:
                print("rec", rec, "hash", hex(hash), "check", hex(ccc))
            if hash != ccc:
                if self.core_verbose > 0:
                    print("Error on hash at rec", rec, "hash", hex(hash), "check", hex(ccc))
                return []

        #print("%5d pos %5d" % (cnt, rec), "hash %8x" % hash, "ok", ok, "len=", blen, end=" ")

        endd = self.getbuffstr(rec + 12 + blen, self.INTSIZE)
        if endd != TwinCore.RECSEP:
            print(" Damaged end data '%s' at" % endd, rec)
            return arr

        rec2 = rec + 16 + blen;
        hash2 = self.getbuffint(rec2)
        blen2 = self.getbuffint(rec2+4)
        data2 = self.getbuffstr(rec2+8, blen2)

        if core_integrity:
            ccc2 = self.hash32(data2)
            if self.core_verbose > 1:
                print("rec", rec, "hash2", hex(hash2), "check2", hex(ccc2))
            if hash2 != ccc2:
                if self.core_verbose > 0:
                    print("Error on hash at rec", rec, "hash2", hex(hash2), "check2", hex(ccc2))
                return []

        arr = [data, data2]
        return arr

    # -------------------------------------------------------------------
    # Originator, dump single record

    def  dump_rec(self, rec, cnt):

        ''' Print record to the screen '''

        cnt2 = 0
        sig = self.getbuffstr(rec, self.INTSIZE)

        if sig == TwinCore.RECDEL:
            if core_showdel:
                blen = self.getbuffint(rec+8)
                data = self.getbuffstr(rec+12, blen)
                print(" Deleted data '%s' at" % sig, rec, "data", trunc(data))
            return cnt2

        if sig != TwinCore.RECSIG:
            if self.core_verbose > 2:
                print(" Damaged data '%s' at" % sig, rec)
            return cnt2

        hash = self.getbuffint(rec+4)
        blen = self.getbuffint(rec+8)

        if blen < 0:
            print("Invalid key length %d at %d" % (blen, rec))
            return cnt2

        data = self.getbuffstr(rec+12, blen)
        if core_integrity:
            ccc = self.hash32(data)
            if self.core_verbose > 1:
                print("rec", rec, "hash", hex(hash), "check", hex(ccc))
            if hash != ccc:
                if self.core_verbose > 0:
                    print("Error on hash at rec", rec, "hash", hex(hash), "check", hex(ccc))
                return []

        endd = self.getbuffstr(rec + 12 + blen, self.INTSIZE)
        if endd != TwinCore.RECSEP:
            print(" Damaged sep data '%s' at" % endd, rec)
            return cnt2

        rec2 = rec + 16 + blen;
        hash2 = self.getbuffint(rec2)
        blen2 = self.getbuffint(rec2+4)

        if blen2 < 0:
            print("Invalid data length %d at %d" % (blen2, rec))
            return cnt2

        data2 = self.getbuffstr(rec2+8, blen2)
        if core_integrity:
            ccc2 = self.hash32(data2)
            if self.core_verbose > 1:
                print("rec", rec, "hash2", hex(hash), "check2", hex(ccc))
            if hash2 != ccc2:
                if self.core_verbose > 0:
                    print("Error on hash at rec", rec, "hash2", hex(hash), "check2", hex(ccc))
                return []
        if self.core_verbose:
            print("%-5d pos %5d" % (cnt, rec), "%8x" % hash, "len", blen, trunc(data),
                                                        "%8x" % hash2,"len", blen2, trunc(data2))
        else:
            print("%-5d pos %5d" % (cnt, rec), "Data:", trunc(data, 18), "Data2:", trunc(data2, 18))

        cnt2 += 1
        return cnt2

    def  check_rec(self, rec):

        ''' Print record to the screen '''
        ret = 0
        sig = self.getbuffstr(rec, self.INTSIZE)

        if sig == TwinCore.RECDEL:
            ret = 1
            # Do not check deleted
            return ret

        if sig != TwinCore.RECSIG:
            if self.core_verbose > 2:
                print(" Damaged data '%s' at" % sig, rec)
            return ret

        hash = self.getbuffint(rec+4)
        blen = self.getbuffint(rec+8)

        if blen < 0:
            if self.core_verbose > 1:
                print("Invalid key length %d at %d" % (blen, rec))
            return ret

        data = self.getbuffstr(rec+12, blen)
        ccc = self.hash32(data)
        if hash != ccc:
            if self.core_verbose > 0:
                print("Error on hash at rec", rec, "hash", hex(hash), "check", hex(ccc))
            return ret

        endd = self.getbuffstr(rec + 12 + blen, self.INTSIZE)
        if endd != TwinCore.RECSEP:
            if self.core_verbose > 1:
                print(" Damaged sep data '%s' at" % endd, rec)
            return ret

        rec2 = rec + 16 + blen;
        hash2 = self.getbuffint(rec2)
        blen2 = self.getbuffint(rec2+4)

        if blen2 < 0:
            print("Invalid data length %d at %d" % (blen2, rec))
            return ret

        data2 = self.getbuffstr(rec2+8, blen2)
        ccc2 = self.hash32(data2)
        if hash2 != ccc2:
            if self.core_verbose > 0:
                print("Error on hash at rec", rec, "hash2", hex(hash), "check2", hex(ccc))
            return ret

        if self.core_verbose > 1:
            print("Record at %d OK." % rec)

        ret += 1
        return ret

    # --------------------------------------------------------------------
    # Internal; no locking

    def  __dump_data(self, lim, skip = 0, dirx = 0):

        ''' Put all data to screen worker function '''

        cnt = skip; cnt2 = 0
        curr = self.getbuffint(CURROFFS)        #;print("curr", curr)
        chash = self.getidxint(CURROFFS)        #;print("chash", chash)
        # Direction sensitivity
        if dirx:
            rrr = range(HEADSIZE + skip * self.INTSIZE * 2, chash, self.INTSIZE * 2)
        else:
            rrr = range(chash - self.INTSIZE * 2, HEADSIZE  - self.INTSIZE * 2, -self.INTSIZE * 2)

        for aa in rrr:
            rec = self.getidxint(aa)
            #print(aa, rec)
            if not core_quiet:
                cnt2 += 1
                ret = self.dump_rec(rec, cnt)
                if ret:
                    cnt += 1
                    if cnt >= lim:
                        break

    def  dump_data(self, lim, skip = 0):

        ''' Put all data to screen '''

        self.__dump_data(lim, skip, 1)

    def  revdump_data(self, lim, skip = 0):

        ''' Put all data to screen in reverse order '''

        self.__dump_data(lim, skip)

    def  reindex(self):
        self.waitlock()
        ret = self.__reindex()
        self.dellock()
        return ret

    # --------------------------------------------------------------------

    def  __reindex(self):

        ''' Recover index. Make sure the DB in not in session.  '''

        ret = 0

        curr = self.getbuffint(CURROFFS) - HEADSIZE
        #print("curr", curr)

        reidx = os.path.splitext(self.fname)[0]  + "_tmp_" + ".pidx"
        tempifp = self.softcreate(reidx)
        self.create_idx(tempifp)

        aa =  HEADSIZE
        while 1:
            if aa >= curr + HEADSIZE:
                break

            sig = self.getbuffstr(aa, self.INTSIZE)

            hhh2 = self.getbuffint(aa + 4)
            lenx = self.getbuffint(aa + 8)
            sep =  self.getbuffstr(aa + 12 + lenx, self.INTSIZE)
            len2 =  self.getbuffint(aa + 20 + lenx)
            if self.core_verbose > 2:
                print(aa, "sig", sig, "hhh2", hhh2, "len", lenx, "sep", sep, "len2", len2)
            elif self.core_verbose > 1:
                data =  self.getbuffstr(aa + 12, lenx)
                data2 =  self.getbuffstr(aa + 24 + lenx, len2)
                print(aa, "sig", sig, "data", data, "data2", data2)

            # Update / Append index
            hashpos = self._getint(tempifp, CURROFFS)

            self._putint(tempifp, hashpos, aa)
            self._putint(tempifp, hashpos + self.INTSIZE, hhh2)
            self._putint(tempifp, CURROFFS, tempifp.tell())

            # This is dependent on the database structure
            aa += lenx + len2 + 24
            ret += 1

        # Make it go out of scope
        self.flush()
        self.ifp.close()

        tempifp.flush();    tempifp.close()

        # Now move files
        try:
            os.remove(self.idxname)
        except:
            pass

        #print("rename", reidx, "->", self.idxname)
        os.rename(reidx, self.idxname)

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
            if ddd[aa:aa+4] == TwinCore.RECSIG:
                found = True
                #print("found:", ddd[:aa+4])
                vacerrfp.write(ddd[:aa])
                break
        if not found:
            vacerrfp.write(ddd)

    # ----------------------------------------------------------------

    def  vacuum(self):

        ''' Remove all deleted data
        Make sure the db in not in session. '''

        ret = 0
        vacname = os.path.splitext(self.fname)[0] + "_vac_" + ".pydb"
        vacerr  = os.path.splitext(self.fname)[0] +  ".perr"
        vacidx = os.path.splitext(vacname)[0]  + ".pidx"
        #print("vacname", vacname)
        #print("vacidx", vacidx)
        #print("vacerr", vacerr)

        # Open for append
        vacerrfp = self.softcreate(vacerr, False)
        vacerrfp.seek(0, os.SEEK_END)

        self.waitlock()

        try:
            # Make sure they are empty
            os.remove(vacname)
            os.remove(vacidx)
        except:
            pass

        # This looks line an unneeded if ...
        # It is used to raise the scope so vacuumed DB closes

        if 1:
            vacdb = TwinCore(vacname)
            vacdb.waitlock()
            #print("vacdb vacidx", vacdb.idxname)
            skip = 0
            curr = self.getbuffint(CURROFFS)               #;print("curr", curr)
            chash = self.getidxint(CURROFFS)               #;print("chash", chash)
            #rrr = range(chash - self.INTSIZE * 2, HEADSIZE  - self.INTSIZE * 2, -self.INTSIZE * 2):
            rrr = range(HEADSIZE + skip * self.INTSIZE * 2, chash, self.INTSIZE * 2)
            for aa in rrr:
                rec = self.getidxint(aa)
                sig = self.getbuffstr(rec, self.INTSIZE)
                if sig == TwinCore.RECDEL:
                    ret += 1
                    if core_pgdebug > 1:
                        print("deleted", rec)
                elif sig != TwinCore.RECSIG:
                    if self.core_verbose:
                        print("Detected error at %d" % rec)
                    self.__save_error(rec, vacerrfp)
                else:
                    global core_integrity
                    tmpi = core_integrity
                    core_integrity = True
                    arr = self.get_rec_offs(rec)
                    core_integrity = tmpi

                    if core_pgdebug > 1:
                        print("vac", rec, arr)

                    if len(arr) > 1:
                        hhh2 = self.hash32(arr[0])
                        hhh3 = self.hash32(arr[1])
                        vacdb.__save_data(hhh2, arr[0], hhh3, arr[1])
                        ret += 1
                    else:
                        # This could be from empty bacause of hash error
                        self.__save_error(rec, vacerrfp)
                        if core_pgdebug > 0:
                            print("Error on vac: %d" % rec)

            vacdb.dellock()

        self.dellock()

        # Any vacummed?
        if ret > 0:
            # Make it go out of scope
            self.flush()
            self.fp.close(); self.ifp.close()

            # Now move files
            try:
                os.remove(self.fname);  os.remove(self.idxname)
            except:
                pass

            if core_pgdebug > 1:
                print("rename", vacname, "->", self.fname)
                print("rename", vacidx, "->", self.idxname)

            os.rename(vacname, self.fname)
            os.rename(vacidx, self.idxname)

            self.waitlock()
            self.fp = self.softcreate(self.fname)
            self.ifp = self.softcreate(self.idxname)
            self.dellock()
        else:
            # Just remove non vacuumed files
            if core_pgdebug > 1:
                print("deleted", vacname, vacidx)
            try:
                os.remove(vacname)
                os.remove(vacidx)
            except:
                pass

        #print("ended vacuum")
        return ret

    def flush(self):
        self.fp.flush()
        self.ifp.flush()

    def  get_rec(self, recnum):
        rsize = self.getdbsize()
        if recnum >= rsize:
            #print("Past end of data.");
            raise  RuntimeError( \
                    "Past end of Data. Asking for %d Max is %d records." \
                                     % (recnum, rsize) )
            return []

        chash = self.getidxint(CURROFFS)
        #print("chash", chash)
        offs = self.getidxint(HEADSIZE + recnum * self.INTSIZE * 2)

        #print("offs", offs)
        return self.rec2arr(offs)

    def  get_rec_offs(self, recoffs):

        rsize = self.getsize(self.fp)
        if recoffs >= rsize:
            #print("Past end of data.");
            raise  RuntimeError( \
                    "Past end of File. Asking for offset %d file size is %d." \
                                     % (recoffs, rsize) )
            return []

        sig = self.getbuffstr(recoffs, self.INTSIZE)
        if sig == TwinCore.RECDEL:
            if core_showdel:
                print("Deleted record.")
            return []
        if sig != TwinCore.RECSIG:
            print("Unlikely offset %d is not at record boundary." % recoffs, sig)
            return []
        #print("recoffs", recoffs)
        return self.rec2arr(recoffs)

    def  del_rec(self, recnum):
        rsize = self.getdbsize()
        if recnum >= rsize:
            if self.core_verbose:
                print("Past end of data.");
            return False
        chash = self.getidxint(CURROFFS)
        #print("chash", chash)
        offs = self.getidxint(HEADSIZE + recnum * self.INTSIZE * 2)
        #print("offs", offs)
        old = self.getbuffstr(offs, self.INTSIZE)
        if old == TwinCore.RECDEL:
            if self.core_verbose:
                print("Record at %d already deleted." % offs);
            return False

        self.putbuffstr(offs, TwinCore.RECDEL)
        return True

    def  del_rec_offs(self, recoffs):

        rsize = self.getsize(self.fp)
        if recoffs >= rsize:
            #print("Past end of data.");
            raise  RuntimeError( \
                    "Past end of File. Asking for offset %d file size is %d." \
                                     % (recoffs, rsize) )
            return False

        sig = self.getbuffstr(recoffs, self.INTSIZE)
        if sig != TwinCore.RECSIG  and sig != TwinCore.RECDEL:
            print("Unlikely offset %d is not at record boundary." % recoffs, sig)
            return False

        self.putbuffstr(recoffs, TwinCore.RECDEL)
        return True

    # Check integrity

    def integrity(self, skip = 0):

        ret = 0; cnt2 = 0
        chash = self.getidxint(CURROFFS)        #;print("chash", chash)
        # Direction sensitivity
        rrr = range(HEADSIZE + skip * self.INTSIZE * 2, chash, self.INTSIZE * 2)
        for aa in rrr:
            rec = self.getidxint(aa)
            #print(aa, rec)
            cnt2 += 1
            ret  += self.check_rec(rec)
        return ret == cnt2

    # Retrive in reverse, limit it

    def  retrieve(self, hashx, limx = 1):

        hhhh = self.hash32(hashx.encode("cp437", errors='replace'))   #;print("hashx", hashx, hhhh)
        chash = self.getidxint(CURROFFS)            #;print("chash", chash)
        arr = []

        self.waitlock()

        #for aa in range(HEADSIZE + self.INTSIZE * 2, chash, self.INTSIZE * 2):
        for aa in range(chash - self.INTSIZE * 2, HEADSIZE  - self.INTSIZE * 2, -self.INTSIZE * 2):
            rec = self.getidxint(aa)
            sig = self.getbuffstr(rec, self.INTSIZE)
            if sig == TwinCore.RECDEL:
                if core_showdel:
                    print(" Deleted record '%s' at" % sig, rec)
            elif sig != TwinCore.RECSIG:
                print(" Damaged data '%s' at" % sig, rec)
            else:
                hhh = self.getbuffint(rec+4)
                if hhh == hhhh:
                    arr.append(self.get_rec_offs(rec))
                    if len(arr) >= limx:
                        break
        self.dellock()

        return arr

    # Find by string matching substring
    def  findrec(self, strx, limx = 1):

        chash = self.getidxint(CURROFFS)            #;print("chash", chash)
        arr = []
        strx2 = strx.encode("cp437", errors='replace');

        self.waitlock()

        #for aa in range(HEADSIZE + self.INTSIZE * 2, chash, self.INTSIZE * 2):
        for aa in range(chash - self.INTSIZE * 2, HEADSIZE  - self.INTSIZE * 2, -self.INTSIZE * 2):
            rec = self.getidxint(aa)
            sig = self.getbuffstr(rec, self.INTSIZE)
            if sig == TwinCore.RECDEL:
                if core_showdel:
                    print(" Deleted record '%s' at" % sig, rec)
            elif sig != TwinCore.RECSIG:
                print(" Damaged data '%s' at" % sig, rec)
            else:
                blen = self.getbuffint(rec+8)
                data = self.getbuffstr(rec + 12, blen)
                if self.core_verbose:
                    print("find buffer", data, strx)
                if strx2 == data:
                    arr.append(self.get_rec_offs(rec))
                    if len(arr) >= limx:
                        break
        self.dellock()

        return arr

    # --------------------------------------------------------------------
    # Search from the end, so latest comes first

    def  find_key(self, hashx, limx = 0xffffffff):

        hhhh = self.hash32(hashx.encode("cp437", errors='replace'))
        #print("hashx", hashx, hhhh)
        chash = self.getidxint(CURROFFS)
        #print("chash", chash)
        arr = []

        self.waitlock()

        #for aa in range(HEADSIZE + self.INTSIZE * 2, chash, self.INTSIZE * 2):
        for aa in range(chash - self.INTSIZE * 2, HEADSIZE  - self.INTSIZE * 2, -self.INTSIZE * 2):
            rec = self.getidxint(aa)
            sig = self.getbuffstr(rec, self.INTSIZE)
            if sig == TwinCore.RECDEL:
                if core_showdel:
                    print("Deleted record '%s' at" % sig, rec)
            elif sig != TwinCore.RECSIG:
                print(" Damaged data '%s' at" % sig, rec)
            else:
                hhh = self.getbuffint(rec+4)
                if hhh == hhhh:
                    arr.append(rec)
                    if len(arr) >= limx:
                        break
        self.dellock()

        return arr


    def  del_data(self, hash, skip = 1):

        ''' Delete data by hash '''

        cnt = skip
        hhhh = int(hash, 16)                #;print("hash", hash, hhhh)
        curr = self.getbuffint(CURROFFS)    #;print("curr", curr)
        chash = self.getidxint(CURROFFS)    #;print("chash", chash)

        arr = []
        for aa in range(HEADSIZE + skip * self.INTSIZE * 2, chash, self.INTSIZE * 2):
            rec = self.getidxint(aa)

            # Optional check
            #sig = self.getbuffstr(rec, self.INTSIZE)
            #if sig != TwinCore.RECSIG:
            #    print(" Damaged data '%s' at" % sig, rec)

            #blen = self.getbuffint(rec+8)
            #print("data '%s' at" % sig, rec, "blen", blen)

            hhh = self.getbuffint(rec+4)
            if hash == hhh:
                if self.core_verbose > 0:
                    print("Would delete", hhh)

            self.putbuffstr(rec, TwinCore.RECDEL)

            cnt += 1

        return arr


    def  del_recs(self, strx, skip = 0, maxrec = INT_MAX):

        ''' Delete records by key string; needs bin str, converted autoamically on entry  '''

        if type(strx) == str:
            strx = strx.encode("cp437")

        cnt = 0;
        chash = self.getidxint(CURROFFS)    #;print("chash", chash)
        for aa in range(HEADSIZE + self.INTSIZE * 2, chash, self.INTSIZE * 2):
            rec = self.getidxint(aa)
            sig = self.getbuffstr(rec, self.INTSIZE)
            if sig == TwinCore.RECDEL:
                if core_showdel:
                    print(" Deleted record '%s' at" % sig, rec)
            elif sig != TwinCore.RECSIG:
                print(" Damaged data '%s' at" % sig, rec)
            else:
                blen = self.getbuffint(rec+8)
                data = self.getbuffstr(rec + 12, blen)
                if self.core_verbose:
                    print("del_recs", data, strx)

                if strx == data:
                    if self.core_verbose > 0:
                        print("Deleting", aa, data)
                    self.putbuffstr(rec, TwinCore.RECDEL)
                    cnt += 1
                    if cnt >= maxrec:
                        break
        return cnt

    # --------------------------------------------------------------------
    # Save data to database file

    def  save_data(self, arg2, arg3):

        # Prepare all args, if cannot encode, use original
        try:
            arg2e = arg2.encode("cp437", errors='replace');
        except:
            arg2e = arg2
        try:
            arg3e = arg3.encode("cp437", errors='replace')
        except:
            arg3e = arg3

        if core_pgdebug > 1:
            print("args", arg2e, "arg3", arg3e)

        hhh2 = self.hash32(arg2e)
        hhh3 = self.hash32(arg3e)

        if core_pgdebug > 1:
            print("hhh2", hhh2, "hhh3", hhh3)

        self.waitlock()
        ret = self.__save_data(hhh2, arg2e, hhh3, arg3e)
        self.dellock()
        return ret

    def __save_data(self, hhh2, arg2e, hhh3, arg3e):

        curr = self.getbuffint(CURROFFS)
        #print("curr", curr)

        # Update / Append data
        tmp = TwinCore.RECSIG
        tmp += struct.pack("I", hhh2)
        tmp += struct.pack("I", len(arg2e))
        tmp += arg2e
        tmp += TwinCore.RECSEP
        tmp += struct.pack("I", hhh3)
        tmp += struct.pack("I", len(arg3e))
        tmp += arg3e

        #print(tmp)

        # The pre assemple to string added 20% efficiency
        self.fp.seek(curr)
        self.fp.write(tmp)

        # Update lenght
        self.putbuffint(CURROFFS, self.fp.tell()) #// - dlink + DATA_LIM)

        hashpos = self.getidxint(CURROFFS)
        #print("hashpos", hashpos)

        # Update / Append index
        self.putidxint(hashpos, curr)
        self.putidxint(hashpos + self.INTSIZE, hhh2)
        self.putidxint(CURROFFS, self.ifp.tell())

        return curr

__all__ = ["TwinCore", "self.core_verbose", "core_quiet", "core_pgdebug", "core_lcktimeout"]

# EOF
