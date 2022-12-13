#!/usr/bin/env python3

import  os, sys, getopt, signal, select, socket, time, struct
import  random, stat, os.path, datetime, threading
# warnings

import struct, io

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GObject
from gi.repository import GLib

DIRTY_MAX   = 0xffffffff

INTSIZE     = 4
HEADSIZE    = 32
CURROFFS    = 16
FIRSTHASH   = HEADSIZE
FIRSTDATA   = HEADSIZE

# Accessed from main file
core_verbose = 0
core_quiet = 0

# ------------------------------------------------------------------------
# Data file and index file; protected by locks
# The TWIN refers to separate files for data / index

class DbTwinCore():

    # These are all four bytes, one can read it like integers

    FILESIG     = b"PYDB"
    IDXSIG      = b"PYIX"
    RECSIG      = b"RECB"
    RECSEP      = b"RECS"
    RECEND      = b"RECE"

    def __init__(self, fname):

        #print("initializing core with", fname)
        self.cnt = 0

        self.dirtyarr = []; self.idirtyarr = []

        self.fname = fname
        self.idxname = os.path.splitext(self.fname)[0] + ".pidx"
        self.lckname = os.path.splitext(self.fname)[0] + ".lock"

        if core_verbose:
            print("fname", fname, "idxname", self.idxname, "lockname", self.lckname)

        self.__waitlock()

        self.fp = self.__softcreate(self.fname)
        self.ifp = self.__softcreate(self.idxname)

        #self.buffer = io.BytesIO(self.fp.read(HEADSIZE))
        #self.index = io.BytesIO(self.ifp.read(HEADSIZE))

        buffsize = self.getsize(self.fp)
        # Initial file creation
        if buffsize < HEADSIZE:
            #print("initial padding")
            self.fp.write(bytearray(HEADSIZE))

            self.fp.seek(0)
            self.fp.write(DbTwinCore.FILESIG)
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
            self.ifp.write(DbTwinCore.IDXSIG)
            self.ifp.write(struct.pack("I", 0xaabbccdd))
            self.ifp.write(struct.pack("B", 0xaa))
            self.ifp.write(struct.pack("B", 0xbb))
            self.ifp.write(struct.pack("B", 0xcc))
            self.ifp.write(struct.pack("B", 0xdd))
            self.ifp.write(struct.pack("B", 0xff))

            self.putidxint(CURROFFS, HEADSIZE)

        #print("buf", self.getbuffstr(0, 4))
        #print("packed", DbTwinCore.FILESIG )

        if  self.getbuffstr(0, 4) != DbTwinCore.FILESIG:
            print("Invalid data signature")
            self.__dellock()
            raise  RuntimeError("Invalid database signature.")

        #print("buffsize", buffsize, "indexsize", indexsize)

        self.__dellock()

    def __del__(self):
        #print("del twincore", self.fp)

        # These will go out of scope automatically
        self.fp.close()
        self.ifp.close()

    def __softcreate(self, fname):
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

    # Simple file system based locking system
    def __waitlock(self):
        cnt = 0
        while True:
            if os.path.isfile(self.lckname):
                #print("__waitlock")
                cnt += 1
                time.sleep(0.1)
                # Taking too long; break in
                if cnt > 3:
                    print("Warn: __waitlock breaking lock")
                    self.__dellock()
                    break
            else:
                self.__softcreate(self.lckname)
                break

    def __dellock(self):
        try:
            os.unlink(self.lckname)
        except:
            pass

    # Deliver a 32 bit hash of whatever
    def _hash32(self, strx):
        lenx = len(strx);  hashx = int(0)
        for aa in strx:
            bb = ord(aa)
            hashx +=  int((bb << 12) + bb)
            hashx &= 0xffffffff
            hashx = int(hashx << 8) + int(hashx >> 8)
            hashx &= 0xffffffff
        return hashx

    def getsize(self, buffio):
        pos = buffio.tell()
        endd = buffio.seek(0, io.SEEK_END)
        buffio.seek(pos, io.SEEK_SET)
        return endd

    # --------------------------------------------------------------------
    # Read / write index / data

    def getidxint(self, offs):
        #print("getidxint", offs)
        val = self.iread(offs, 4)
        return struct.unpack("I", val)[0]

    def putidxint(self, offs, val):
        #print("putidxint", offs, val)
        self.ifp.seek(offs, io.SEEK_SET)
        pp = struct.pack("I", val)
        self.iwrite(pp)

    def putbuffint(self, offs, val):
        #print("putbuffint", offs, val)
        self.fp.seek(offs, io.SEEK_SET)
        cc = struct.pack("I", val)
        self.dwrite(cc)

    def getbuffint(self, offs):
        self.fp.seek(offs, io.SEEK_SET)
        val = self.fp.read(4)
        return struct.unpack("I", val)[0]

    def getbuffstr(self, offs, xlen):
        self.fp.seek(offs, io.SEEK_SET)
        val = self.fp.read(xlen)
        return val

    def putbuffstr(self, offs, xstr):
        self.fp.seek(offs, io.SEEK_SET)
        val = self.buffer.dwrite(xstr)

    # --------------------------------------------------------------------
    # Data: Mark dirty automatically

    def  dwrite(self, var):
        bb = self.fp.tell()
        self.fp.write(var)
        ee = self.fp.tell()
        self.dirtyarr.append((bb, ee))

    # Read index; if past stream eof, read from file
    def  iread(self, offs, lenx):
        self.ifp.seek(offs, io.SEEK_SET)
        ret = self.ifp.read(lenx)
        return ret

    # --------------------------------------------------------------------
    # Index: Mark dirty automatically

    def  iwrite(self, var):
        ibb = self.ifp.tell()
        self.ifp.write(var)
        iee = self.ifp.tell()
        self.idirtyarr.append((ibb, iee))

    def  dump_rec(self, rec, cnt):

        #sig = self.getbuffint(rec)
        #self.cnt += 1
        sig = self.getbuffstr(rec, INTSIZE)
        if sig != DbTwinCore.RECSIG:
            print("Damaged data '%s' at" % sig, rec)

        hash = self.getbuffint(rec+4)
        blen = self.getbuffint(rec+8)

        if hash & 0x8000000:
            ok = 1
        else:
            ok = 0

        print("%5d pos %5d" % (cnt, rec), "hash %8x" % hash, "ok", ok, "len=", blen, end=" ")

        data = self.getbuffstr(rec+12, blen)
        #data = self.buffer.getbuffer()[rec+12:rec+12+blen]
        #print("buff", data)
        #self.buffer.getbuffer()[rec+12+blen:rec+12+blen+4]

        endd = self.getbuffstr(rec + 12 + blen, INTSIZE)
        if endd != DbTwinCore.RECSEP:
            print("Damaged end data '%s' at" % endd, rec)

        rec2 = rec + 12 + blen;
        hash2 = self.getbuffint(rec2)
        blen2 = self.getbuffint(rec2+4)
        data2 = self.getbuffstr(rec2+8, blen2)

        print("buff =", data, "buff2 =", data2)
        #print()

        #print("hash2", hex(hash2), "len2=", blen2)

    def  dump_data(self, lim, skip = 0):

        #global core_quiet
        #print ("core_quiet", core_quiet)

        curr = self.getbuffint(CURROFFS)
        #print("curr", curr)
        chash = self.getidxint(CURROFFS)
        #print("chash", chash)

        cnt = skip;
        for aa in range(HEADSIZE + skip * INTSIZE * 2, chash, INTSIZE * 2):
            rec = self.getidxint(aa)
            #print(aa, rec)

            if not core_quiet:
                self.dump_rec(rec, cnt)
            cnt += 1
            if cnt >= lim:
                break

    # --------------------------------------------------------------------
    # Save data to database file

    def  save_data(self, arg2, arg3):

        self.__waitlock()

        hhh = self._hash32(arg2)
        # Mark it as good
        hhh |= 0x8000000
        #print("hash", hex(hhh))

        #print("args", arg2, "---", arg3)
        curr = self.getbuffint(CURROFFS)
        #print("curr", curr)

        # Update / Append data
        tmp = DbTwinCore.RECSIG
        tmp += struct.pack("I", hhh)
        tmp += struct.pack("I", len(arg2))
        tmp += arg2.encode("cp437")
        tmp += DbTwinCore.RECSEP
        tmp += struct.pack("I", len(arg3))
        tmp += arg3.encode("cp437")
        #print(tmp)

        # Assemple to string added 20% efficiency
        self.fp.seek(curr)
        self.dwrite(tmp)

        # Update lenght
        self.putbuffint(CURROFFS, self.fp.tell()) #// - dlink + DATA_LIM)

        hashpos = self.getidxint(CURROFFS)
        #print("hashpos", hashpos)

        # Update / Append index
        self.putidxint(hashpos, curr)
        self.putidxint(hashpos + INTSIZE, hhh)
        self.putidxint(CURROFFS, self.ifp.tell())

        #self.flushx()
        self.__dellock()

    # --------------------------------------------------------------------
    # Simplify array to connect overlapping ranges. This minimizes IO
    # onto the file

    def simplify(self, dirtarr, thresh = 4):

        #print("simplify",  dirtarr)

        darr = []; old_aa = 0; old_bb = 0
        save_aa = DIRTY_MAX; save_bb = 0;

        for aa, bb in dirtarr:
            if abs(aa - old_bb) > thresh:
                if save_aa != DIRTY_MAX:
                    darr.append((save_aa, save_bb))
                    save_aa = DIRTY_MAX; save_bb = 0
            if save_aa > aa:
                save_aa = aa
            if save_bb < bb:
                save_bb = bb
            old_aa = aa; old_bb = bb

        # Last, append if any
        if save_aa != DIRTY_MAX:
            darr.append((save_aa, save_bb))

        #print(darr)
        return darr;

    # Flush all arrays onto their respective files

    def flushx(self):

        # Save buffers from
        #print(self.dirtyarr)

        #darr = self.simplify(self.dirtyarr)
        #for aa, bb in darr:
        #    self.fp.seek(aa)
        #    self.fp.write(self.buffer.getbuffer()[aa:bb])
        #self.dirtyarr = []
        #
        ##print(self.idirtyarr)
        #idarr = self.simplify(self.idirtyarr)
        ##print(idarr)
        #
        #for aa, bb in idarr:
        #    self.ifp.seek(aa)
        #    self.ifp.write(self.index.getbuffer()[aa:bb])
        #self.idirtyarr = []
        pass

__all__ = ["DbTwinCore", "HEADSIZE", "core_verbose"]

# EOF
