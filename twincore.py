#!/usr/bin/env python3

'''
    Twincore;
    The reason for this name is that two files are created to contain the data.
    The first contains the data, the second contains the offsets (indexes) and hashes.
    The second file can be re-built easily from the first.

    Structure of the data:

    32 byte header, starating with FILESIG

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

'''

import  os, sys, getopt, signal, select, socket, time, struct
import  random, stat, os.path, datetime, threading
import  struct, io

DIRTY_MAX   = 0xffffffff

INTSIZE     = 4
HEADSIZE    = 32
CURROFFS    = 16
FIRSTHASH   = HEADSIZE
FIRSTDATA   = HEADSIZE

# Accessed from main file
core_verbose = 0
core_quiet = 0
core_pgdebug = 0
core_showdel = 0

def trunc(strx, num = 8):
    ''' truncate for printing nicely '''
    if len(strx) > num:
        strx = strx[:num] + b".."
    return strx


class TwinCoreBase():

    ''' This class provides basis services to twincore. '''

    def __init__(self):
        #print("initializing core base")
        pass
        self.fp = None
        self.ifp = None

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


    # Simple file system based locking system
    def waitlock(self):
        cnt = 0
        while True:
            if os.path.isfile(self.lckname):
                #print("waitlock")
                cnt += 1
                time.sleep(0.1)
                # Taking too long; break in
                if cnt > 3:
                    print("Warn: waitlock breaking lock", self.lckname)
                    self.dellock()
                    break
            else:
                self.softcreate(self.lckname)
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
            bb = aa
            hashx +=  int( (bb << 12) + bb)
            hashx &= 0xffffffff
            hashx = int(hashx << 8) + int(hashx >> 8)
            hashx &= 0xffffffff
        return hashx

    def softcreate(self, fname):
        fp = None
        try:
            fp = open(fname, "rb+")
        except:
            try:
                fp = open(fname, "wb+")
            except:
                print("Cannot open /create ", fname, sys.exc_info())
                raise
        return fp

 # ------------------------------------------------------------------------
# Data file and index file; protected by locks
# The TWIN refers to separate files for data / index

class TwinCore(TwinCoreBase):

    # These are all four bytes, one can read it like integers

    FILESIG     = b"PYDB"
    IDXSIG      = b"PYIX"
    RECSIG      = b"RECB"
    RECDEL      = b"RECX"
    RECSEP      = b"RECS"
    RECEND      = b"RECE"

    def __init__(self, fname):

        super(TwinCoreBase, self).__init__()
        #print("initializing core with", fname)

        self.cnt = 0
        self.fname = fname
        self.idxname = os.path.splitext(self.fname)[0] + ".pidx"
        self.lckname = os.path.splitext(self.fname)[0] + ".lock"

        self.lasterr = ""

        #if core_verbose:
        #    print("fname", fname, "idxname", self.idxname, "lockname", self.lckname)

        self.waitlock()

        self.fp = self.softcreate(self.fname)
        self.ifp = self.softcreate(self.idxname)

        buffsize = self.getsize(self.fp)

        # Initial file creation
        if buffsize < HEADSIZE:
            #print("initial padding")
            self.fp.write(bytearray(HEADSIZE))

            self.fp.seek(0)
            self.fp.write(TwinCore.FILESIG)
            self.fp.write(struct.pack("B", 0x03))
            self.fp.write(struct.pack("I", 0xaabbccdd))
            self.fp.write(struct.pack("B", 0xaa))
            self.fp.write(struct.pack("B", 0xbb))
            self.fp.write(struct.pack("B", 0xcc))
            self.fp.write(struct.pack("B", 0xdd))
            self.fp.write(struct.pack("B", 0xff))

            self.putbuffint(CURROFFS, HEADSIZE)

        indexsize = self.getsize(self.ifp)
        # Initial file creation
        if indexsize < HEADSIZE:
            #print("initial padding")
            self.ifp.write(bytearray(HEADSIZE))

            self.ifp.seek(0)
            self.ifp.write(TwinCore.IDXSIG)
            self.ifp.write(struct.pack("I", 0xaabbccdd))
            self.ifp.write(struct.pack("B", 0xaa))
            self.ifp.write(struct.pack("B", 0xbb))
            self.ifp.write(struct.pack("B", 0xcc))
            self.ifp.write(struct.pack("B", 0xdd))
            self.ifp.write(struct.pack("B", 0xff))

            self.putidxint(CURROFFS, HEADSIZE)

        if  self.getbuffstr(0, 4) != TwinCore.FILESIG:
            print("Invalid data signature")
            self.dellock()
            raise  RuntimeError("Invalid database signature.")
        #print("buffsize", buffsize, "indexsize", indexsize)
        self.dellock()

    def getdbsize(self):
        chash = self.getidxint(CURROFFS) - HEADSIZE
        return int(chash / (2 * INTSIZE))

    # --------------------------------------------------------------------
    def rec2arr(self, rec):

        arr = []
        sig = self.getbuffstr(rec, INTSIZE)
        if sig != TwinCore.RECSIG:
            if sig != TwinCore.RECDEL:
                print("Damaged data '%s' at" % sig, rec)
                return arr

        hash = self.getbuffint(rec+4)
        blen = self.getbuffint(rec+8)
        data = self.getbuffstr(rec + 12, blen)

        #print("hash", hash, "check", self.hash32(data))
        #print("%5d pos %5d" % (cnt, rec), "hash %8x" % hash, "ok", ok, "len=", blen, end=" ")

        endd = self.getbuffstr(rec + 12 + blen, INTSIZE)
        if endd != TwinCore.RECSEP:
            print("Damaged end data '%s' at" % endd, rec)
            return arr

        rec2 = rec + 16 + blen;
        hash2 = self.getbuffint(rec2)
        blen2 = self.getbuffint(rec2+4)
        data2 = self.getbuffstr(rec2+8, blen2)

        #print("hash2", hash2, "check2", self.hash32(data2))

        arr = [data, data2]
        return arr

    # -------------------------------------------------------------------
    # originator

    def  dump_rec(self, rec, cnt):

        ''' Print record to the screen '''
        cnt2 = 0
        sig = self.getbuffstr(rec, INTSIZE)

        if sig == TwinCore.RECDEL:
            if core_showdel:
                blen = self.getbuffint(rec+8)
                data = self.getbuffstr(rec+12, blen)
                print(" Deleted data '%s' at" % sig, rec, "data", trunc(data))
            return cnt2

        if sig != TwinCore.RECSIG:
            if core_verbose:
                print("Damaged data '%s' at" % sig, rec)
            return cnt2

        hash = self.getbuffint(rec+4)
        blen = self.getbuffint(rec+8)

        if blen < 0:
            print("Invalid key length %d at %d" % (blen, rec))
            return cnt2

        data = self.getbuffstr(rec+12, blen)

        endd = self.getbuffstr(rec + 12 + blen, INTSIZE)
        if endd != TwinCore.RECSEP:
            print("Damaged end data '%s' at" % endd, rec)
            return cnt2

        rec2 = rec + 16 + blen;
        hash2 = self.getbuffint(rec2)
        blen2 = self.getbuffint(rec2+4)

        if blen2 < 0:
            print("Invalid data length %d at %d" % (blen2, rec))
            return cnt

        data2 = self.getbuffstr(rec2+8, blen2)

        if core_verbose:
            print("%-5d pos %5d" % (cnt, rec), "%8x" % hash, "len", blen, trunc(data),
                                                        "%8x" % hash2,"len", blen2, trunc(data2))
        else:
            print("%-5d pos %5d" % (cnt, rec), "Data:", trunc(data, 18), "Data2:", trunc(data2, 18))

        cnt2 += 1

        return cnt2

    def  dump_data(self, lim, skip = 0):

        ''' Put all data to screen '''

        cnt = skip; cnt2 = 0
        curr = self.getbuffint(CURROFFS)
        #print("curr", curr)
        chash = self.getidxint(CURROFFS)
        #print("chash", chash)
        for aa in range(HEADSIZE + skip * INTSIZE * 2, chash, INTSIZE * 2):
            rec = self.getidxint(aa)
            cnt2 += 1
            #print(aa, rec)
            if not core_quiet:
                ret = self.dump_rec(rec, cnt)
                if ret:
                    cnt += 1
                    if cnt >= lim:
                        break

    def  revdump_data(self, lim, skip = 0):

        ''' Put all data to screen in reverse order'''
        curr = self.getbuffint(CURROFFS)
        #print("curr", curr)
        chash = self.getidxint(CURROFFS)
        #print("chash", chash)
        cnt = 0; cnt2 = 0
        for aa in range(chash - INTSIZE * 2, HEADSIZE  - INTSIZE * 2, -INTSIZE * 2):
            rec = self.getidxint(aa)
            #print(aa, rec)
            if not core_quiet:
                cnt2 += 1
                ret = self.dump_rec(rec, cnt)
                if ret:
                    cnt += 1
                    if cnt >= lim:
                        break


    def  recover(self):

        ''' Recover index
            Make sure the db in not in session.
        '''

        ret = 0

        self.waitlock()

        curr = self.getbuffint(CURROFFS) - HEADSIZE
        #print("curr", curr)

        aa =  HEADSIZE
        while 1:
            if aa >= curr:
                break
            sig = self.getbuffstr(aa, INTSIZE)


            lenx = self.getbuffint(aa + 8)
            sep =  self.getbuffstr(aa + 12 + lenx, INTSIZE)
            len2 =  self.getbuffint(aa + 20 + lenx)
            print(aa, "sig", sig, "len", lenx, "sep", sep, "len2", len2)
            aa += lenx + len2 + 24
            #ret += 1

            # Build index (TODO


        self.dellock()
        return ret

    def  vacuum(self):

        ''' Remove all deleted data
            Make sure the db in not in session.
        '''

        ret = 0

        self.waitlock()

        vacname = os.path.splitext(self.fname)[0] + "_vac_" + ".pydb"
        vacidx = os.path.splitext(vacname)[0]  + ".pidx"

        #print("vacname", vacname)
        #print("vacidx", vacidx)

        # This looks line an unneeded if ... raises the scope so vacuumed DB closes
        if 1:
            vacdb = TwinCore(vacname)
            vacdb.waitlock()
            #print("vacdb vacidx", vacdb.idxname)

            curr = self.getbuffint(CURROFFS)
            #print("curr", curr)
            chash = self.getidxint(CURROFFS)
            #print("chash", chash)

            for aa in range(chash - INTSIZE * 2, HEADSIZE  - INTSIZE * 2, -INTSIZE * 2):
                rec = self.getidxint(aa)
                sig = self.getbuffstr(rec, INTSIZE)
                if sig == TwinCore.RECDEL:
                    ret += 1
                    if core_pgdebug:
                        print("deleted", rec)
                else:
                    arr = self.get_rec_offs(rec)
                    if core_pgdebug:
                        print("vac", rec, arr)

                    hhh2 = self.hash32(arr[0])
                    hhh3 = self.hash32(arr[1])
                    vacdb.__save_data(hhh2, arr[0], hhh3, arr[1])

            vacdb.dellock()

        self.dellock()

        # Any vacummed?
        if ret > 0:
            # Make it go out of scope
            self.flush()
            self.fp.close(); self.ifp.close()

            # Now move files
            os.remove(self.fname);  os.remove(self.idxname)

            #print("rename", vacname, "->", self.fname)
            #print("rename", vacidx, "->", self.idxname)

            os.rename(vacname, self.fname)
            os.rename(vacidx, self.idxname)

            self.waitlock()
            self.fp = self.softcreate(self.fname)
            self.ifp = self.softcreate(self.idxname)
            self.dellock()

        else:
            # Just remove non vacuumed files
            #print("deleted", vacname, vacidx)
            os.remove(vacname)
            os.remove(vacidx)

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
        offs = self.getidxint(HEADSIZE + recnum * INTSIZE * 2)
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

        sig = self.getbuffstr(recoffs, INTSIZE)
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
            if core_verbose:
                print("Past end of data.");
            return False
        chash = self.getidxint(CURROFFS)
        #print("chash", chash)
        offs = self.getidxint(HEADSIZE + recnum * INTSIZE * 2)
        #print("offs", offs)
        old = self.getbuffstr(offs, INTSIZE)
        if old == TwinCore.RECDEL:
            if core_verbose:
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

        sig = self.getbuffstr(recoffs, INTSIZE)
        if sig != TwinCore.RECSIG  and sig != TwinCore.RECDEL:
            print("Unlikely offset %d is not at record boundary." % recoffs, sig)
            return False

        self.putbuffstr(recoffs, TwinCore.RECDEL)
        return True


    # Retrive in reverse, limit it

    def  retrieve(self, hashx, limx = 1):

        hhhh = self.hash32(hashx.encode("cp437"))
        #print("hashx", hashx, hhhh)
        chash = self.getidxint(CURROFFS)
        #print("chash", chash)
        arr = []

        self.waitlock()

        #for aa in range(HEADSIZE + INTSIZE * 2, chash, INTSIZE * 2):
        for aa in range(chash - INTSIZE * 2, HEADSIZE  - INTSIZE * 2, -INTSIZE * 2):
            rec = self.getidxint(aa)
            sig = self.getbuffstr(rec, INTSIZE)
            if sig == TwinCore.RECDEL:
                if core_showdel:
                    print("Deleted record '%s' at" % sig, rec)
            elif sig != TwinCore.RECSIG:
                print("Damaged data '%s' at" % sig, rec)
            else:
                hhh = self.getbuffint(rec+4)
                if hhh == hhhh:
                    arr.append(self.get_rec_offs(rec))
                    if len(arr) >= limx:
                        break
        self.dellock()

        return arr

    # --------------------------------------------------------------------
    # Search from the back end, so latest comes first

    def  find_key(self, hashx, limx = 0xffffffff):

        hhhh = self.hash32(hashx.encode("cp437"))
        #print("hashx", hashx, hhhh)
        chash = self.getidxint(CURROFFS)
        #print("chash", chash)
        arr = []

        self.waitlock()

        #for aa in range(HEADSIZE + INTSIZE * 2, chash, INTSIZE * 2):
        for aa in range(chash - INTSIZE * 2, HEADSIZE  - INTSIZE * 2, -INTSIZE * 2):
            rec = self.getidxint(aa)
            sig = self.getbuffstr(rec, INTSIZE)
            if sig == TwinCore.RECDEL:
                if core_showdel:
                    print("Deleted record '%s' at" % sig, rec)
            elif sig != TwinCore.RECSIG:
                print("Damaged data '%s' at" % sig, rec)
            else:
                hhh = self.getbuffint(rec+4)
                if hhh == hhhh:
                    arr.append(rec)
                    if len(arr) >= limx:
                        break
        self.dellock()

        return arr

    def  del_data(self, hash, skip):

        cnt = skip
        hhhh = int(hash, 16)
        #print("hash", hash, hhhh)

        curr = self.getbuffint(CURROFFS)
        #print("curr", curr)
        chash = self.getidxint(CURROFFS)
        #print("chash", chash)

        arr = []
        for aa in range(HEADSIZE + skip * INTSIZE * 2, chash, INTSIZE * 2):

            rec = self.getidxint(aa)

            # Optional check
            #sig = self.getbuffstr(rec, INTSIZE)
            #if sig != TwinCore.RECSIG:
            #    print("Damaged data '%s' at" % sig, rec)

            #blen = self.getbuffint(rec+8)
            #print("data '%s' at" % sig, rec, "blen", blen)

            hhh = self.getbuffint(rec+4)
            cnt += 1

        return arr

    # --------------------------------------------------------------------
    # Save data to database file

    def  save_data(self, arg2, arg3):

        # Prepare all args
        arg2e = arg2.encode("cp437")
        arg3e = arg3.encode("cp437")
        #print("args", arg2e, "arg3", arg3e)

        hhh2 = self.hash32(arg2e)
        hhh3 = self.hash32(arg3e)
        #print("hhh2", hhh2, "hhh3", hhh3)

        self.waitlock()
        self.__save_data(hhh2, arg2e, hhh3, arg3e)
        self.dellock()


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
        self.putidxint(hashpos + INTSIZE, hhh2)
        self.putidxint(CURROFFS, self.ifp.tell())

__all__ = ["TwinCore", "core_verbose", "core_quiet"]

# EOF
