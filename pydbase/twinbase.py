#!/usr/bin/env python3

'''!
    twinbase -- extracted from twincore to make it eazier to read
'''

import  os, sys, getopt, signal, select, socket, time, struct
import  random, stat, os.path, datetime
import  struct, io, traceback, hashlib, traceback

try:
    import fcntl
except:
    fcntl = None

base = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(base, '..', 'pydbase'))

from dbutils import *

HEADSIZE        = 32

INT_MAX         = 0xffffffff    ##< INT_MAX in 'C' py has BIG integer
CURROFFS        = 16            ## Sat 04.Feb.2023 deleted
FIRSTHASH       = HEADSIZE      ##< data starts here
FIRSTDATA       = HEADSIZE
LOCK_TIMEOUT    = 20            ##< this is in 0.1 sec units

## These are all four bytes, one can read it like integers

FILESIG     = b"PYDB"
IDXSIG      = b"PYIX"
RECSIG      = b"RECB"
RECDEL      = b"RECX"
RECSEP      = b"RECS"
RECEND      = b"RECE"

VERSION = "1.7.1"

# Accessed from the main file as well

base_locktout   = LOCK_TIMEOUT   # Settable from ...
base_pgdebug    = 0
base_quiet      = 0

class TwinCoreBase():

    ''' This class provides basic services to twincore  '''

    INTSIZE     = 4

    def __init__(self, pgdebug = 0):

        self.pgdebug = pgdebug

        global base_pgdebug
        base_pgdebug = pgdebug
        set_pgdebug(pgdebug)

        if self.pgdebug > 1:
            print("Initializing core base pgdebug =", pgdebug)

        # Provide placeholders
        self.fp = None
        self.ifp = None
        self.cnt = 0

        #self.fname = "" ;        self.idxname = ""
        #self.lckname = "";
        self.lasterr = ""

    def get_version(self):
        ''' Return version sting. '''
        return VERSION

    #def __del__(self):
    #    print("Flushing")

    def getsize(self, buffio):

        ''' get the dabase file size '''

        sss = os.stat(buffio.fileno())
        #print("sss", sss, sss.st_size)
        return sss.st_size

    # --------------------------------------------------------------------
    # Read / write index / data; Data is accessed by int or by str;
    #  Note: data by int is in little endian (intel) order

    def getidxint(self, offs):
        ''' get an integer value from index offset '''
        #print("getidxint", offs)
        self.ifp.seek(offs, io.SEEK_SET)
        val = self.ifp.read(4)
        return struct.unpack("I", val)[0]

    def putidxint(self, offs, val):
        ''' put an integer value to offset '''
        #print("putidxint", offs, val)
        pp = struct.pack("I", val)
        self.ifp.seek(offs, io.SEEK_SET)
        self.ifp.write(pp)

    def getbuffint(self, offs):
        ''' get an integer value from offset '''
        self.fp.seek(offs, io.SEEK_SET)
        val = self.fp.read(4)
        return struct.unpack("I", val)[0]

    def putbuffint(self, offs, val):
        ''' Write an in to buffer '''
        #print("putbuffint", offs, val)
        self.fp.seek(offs, io.SEEK_SET)
        cc = struct.pack("I", val)
        self.fp.write(cc)

    def getbuffstr(self, offs, xlen):
        ''' Get sreing from buffer '''
        self.fp.seek(offs, io.SEEK_SET)
        val = self.fp.read(xlen)
        return val

    def putbuffstr(self, offs, xstr):
        ''' Write a string to buffer '''
        self.fp.seek(offs, io.SEEK_SET)
        val = self.fp.write(xstr)

    def _putint(self, ifp, offs, val):
        pp = struct.pack("I", val)
        ifp.seek(offs, io.SEEK_SET)
        ifp.write(pp)

    #def _getint(self, ifp, offs):
    #    ifp.seek(offs, io.SEEK_SET)
    #    val = ifp.read(4)
    #    return struct.unpack("I", val)[0]

    def hash32(self, strx):

        ''' Deliver a 32 bit hash of the passed entity. Re-written
            to use sha and cut the result to size
            Replaced this with an external hash function for speed.
        '''

        #print("hashing", strx)
        #ttt = time.time()

        hh = hashlib.new("sha256"); hh.update(strx)
        hashx = int(hh.hexdigest()[:8], base=16)

        # Replaced this with an external hash function for speed
        #hashx = 0
        #lenx = len(strx);  hashx = int(0)
        #for aa in strx:
        #    hashx +=  int( (aa << 12) + aa)
        #    hashx &= 0xffffffff
        #    hashx = int(hashx << 8) + int(hashx >> 8)
        #    hashx &= 0xffffffff
        #print("hash32 %.3f" % ((time.time() - ttt) * 1000) )
        #print("hash32: %x" % hashx)

        return hashx

    def _lockx(self, fp):
        if fcntl:
            fcntl.lockf(fp, fcntl.LOCK_EX)
        else:
            import msvcrt
            fnum = fp.fileno()
            msvcrt.locking(fnum, msvcrt.LK_LOCK, os.fstat(fnum).st_size)

    def softcreate(self, fname, raisex = True):

        ''' Open for read / write. Create if needed. '''

        #print("Softcreate", fname)

        fp = None
        try:
            fp = open(fname, "rb+")
            #self._lockx(fp)
        except:
            try:
                fp = open(fname, "wb+")
                self._lockx(fp)
            except:
                #print("Deleting lock", self.lckname)
                #dellock(self.lckname)
                self.lock.unlock()  #dellock(self.lckname)
                print("Cannot open / create ", "'" + fname + "'", sys.exc_info())

                if raisex:
                    raise
                pass

        return fp

    def create_data(self, fp):

        ''' Sub for initial DATA file '''

        fp.write(bytearray(HEADSIZE))

        arrx = []
        arrx.append(FILESIG)
        arrx.append(struct.pack("B", 0x03))
        arrx.append(struct.pack("I", 0xaabbccdd))
        arrx.append(struct.pack("B", 0xaa))
        arrx.append(struct.pack("B", 0xbb))
        arrx.append(struct.pack("B", 0xcc))
        arrx.append(struct.pack("B", 0xdd))
        arrx.append(struct.pack("B", 0xff))

        outx = b"".join(arrx)
        fp.seek(0)
        fp.write(outx)

    def create_idx(self, ifp):

        ''' Sub for initial INDEX file '''

        ifp.write(bytearray(HEADSIZE))

        arrx = []
        arrx.append(IDXSIG)
        arrx.append(struct.pack("I", 0xaabbccdd))
        arrx.append(struct.pack("B", 0xaa))
        arrx.append(struct.pack("B", 0xbb))
        arrx.append(struct.pack("B", 0xcc))
        arrx.append(struct.pack("B", 0xdd))
        arrx.append(struct.pack("B", 0xff))

        outx = b"".join(arrx)
        ifp.seek(0)
        ifp.write(outx)

        #pp = struct.pack("I", HEADSIZE)
        #ifp.seek(CURROFFS, io.SEEK_SET)
        #ifp.write(pp)

# EOF
