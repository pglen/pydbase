#!/usr/bin/env python3

'''!
    twinbase -- extracted from twincore to make it eazier to read
'''

import  os, sys, getopt, signal, select, socket, time, struct
import  random, stat, os.path, datetime, threading
import  struct, io, traceback, fcntl

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

# Accessed from the main file as well

base_pgdebug    = 0
base_locktout   = LOCK_TIMEOUT   # Settable from ...
base_quiet      = 0
base_integrity  = 0
base_showdel    = 0

def dellock(lockname):

    ''' Lock removal;
        Test for stale lock;
    '''

    if base_pgdebug > 1:
        print("Dellock", lockname)

    try:
        if os.path.isfile(lockname):
            os.unlink(lockname)
    except:
        if base_pgdebug > 1:
            #print("Del lock failed", sys.exc_info())
            put_exception("Del Lock")


def waitlock(lockname):

    ''' Wait for lock file to become available. '''

    if base_pgdebug > 1:
        print("Waitlock", lockname)

    cnt = 0
    while True:
        if os.path.isfile(lockname):
            if cnt == 0:
                #try:
                #    fpx = open(lockname)
                #    pid = int(fpx.read())
                #    fpx.close()
                #except:
                #    print("Exception in lock test", sys.exc_info())
                pass
            cnt += 1
            time.sleep(0.1)
            if cnt > base_locktout * 100:
                # Taking too long; break in
                if base_pgdebug > 1:
                    print("Warn: main Lock held too long ... pid =", os.getpid(), cnt)
                dellock(lockname)
                break
        else:
            break

    # Finally, create lock
    xfp = create(lockname)
    xfp.write(str(os.getpid()).encode())
    xfp.close()

class TwinCoreBase():

    ''' This class provides basic services to twincore  '''

    INTSIZE     = 4

    def __init__(self, pgdebug = 0):

        self.pgdebug = pgdebug

        global base_pgdebug
        base_pgdebug = pgdebug

        if self.pgdebug > 1:
            print("Initializing core base pgdebug =", pgdebug)

        # Provide placeholders
        self.fp = None
        self.ifp = None
        self.cnt = 0

        #self.fname = "" ;        self.idxname = ""
        #self.lckname = "";
        self.lasterr = ""

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

    #def _getint(self, ifp, offs):
    #    ifp.seek(offs, io.SEEK_SET)
    #    val = ifp.read(4)
    #    return struct.unpack("I", val)[0]

    def hash32(self, strx):

        ''' Deliver a 32 bit hash of the passed entity '''

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

        #print("Softcreate", fname)

        fp = None
        try:
            fp = open(fname, "rb+")
        except:
            try:
                fp = open(fname, "wb+")
                fcntl.lockf(fp, fcntl.LOCK_EX)
            except:
                #print("Deleting lock", self.lckname)
                dellock(self.lckname)
                print("Cannot open / create ", "'" + fname + "'", sys.exc_info())
                if raisex:
                    raise
                pass

        return fp

    def create_data(self, fp):

        ''' Sub for initial DATA file '''

        fp.write(bytearray(HEADSIZE))

        fp.seek(0)
        fp.write(FILESIG)
        fp.write(struct.pack("B", 0x03))
        fp.write(struct.pack("I", 0xaabbccdd))
        fp.write(struct.pack("B", 0xaa))
        fp.write(struct.pack("B", 0xbb))
        fp.write(struct.pack("B", 0xcc))
        fp.write(struct.pack("B", 0xdd))
        fp.write(struct.pack("B", 0xff))

    def create_idx(self, ifp):

        ''' Sub for initial INDEX file '''

        ifp.write(bytearray(HEADSIZE))

        ifp.seek(0)
        ifp.write(IDXSIG)
        ifp.write(struct.pack("I", 0xaabbccdd))
        ifp.write(struct.pack("B", 0xaa))
        ifp.write(struct.pack("B", 0xbb))
        ifp.write(struct.pack("B", 0xcc))
        ifp.write(struct.pack("B", 0xdd))
        ifp.write(struct.pack("B", 0xff))

        #pp = struct.pack("I", HEADSIZE)
        #ifp.seek(CURROFFS, io.SEEK_SET)
        #ifp.write(pp)


# EOF
