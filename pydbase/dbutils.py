#!/usr/bin/env python3

import datetime, time, traceback, multiprocessing

import sys, os, fcntl

utils_pgdebug  = 0
utils_locktout = 7

locklevel = {}

def set_pgdebug(level):
    global utils_pgdebug
    utils_pgdebug = level

def put_exception(xstr):

    cumm = xstr + " "
    a,b,c = sys.exc_info()
    if a != None:
        cumm += str(a) + " " + str(b) + "\n"
        try:
            #cumm += str(traceback.format_tb(c, 10))
            ttt = traceback.extract_tb(c)
            for aa in ttt:
                cumm += "File: " + os.path.basename(aa[0]) + \
                        "  Line: " + str(aa[1]) + "\n" +  \
                        "    Context: " + aa[2] + " -> " + aa[3] + "\n"
        except:
            print( "Could not print trace stack. ", sys.exc_info())

    print(cumm)

# ------------------------------------------------------------------------
# Get date out of UUID

def uuid2date(uuu):

    UUID_EPOCH = 0x01b21dd213814000
    dd = datetime.datetime.fromtimestamp(\
                    (uuu.time - UUID_EPOCH)*100/1e9)
    #print(dd.timestamp())
    return dd

def uuid2timestamp(uuu):

    UUID_EPOCH = 0x01b21dd213814000
    dd = datetime.datetime.fromtimestamp(\
                    (uuu.time - UUID_EPOCH)*100/1e9)
    return dd.timestamp()

def pad(strx, lenx=8):
    ttt = len(strx)
    if ttt >= lenx:
        return strx
    padx = " " * (lenx-ttt)
    return strx + padx

def decode_data(self, encoded):

    try:
        bbb = self.packer.decode_data(encoded)
    except:
        print("Cannot decode", sys.exc_info())
        bbb = ""
    return bbb

class   FileLock():

    ''' A working file lock in Linux '''

    def __init__(self, lockname):

        ''' Create the lock file '''

        if not lockname:
            raise ValuError("Must specify lockfile")

        self.lockname = lockname
        try:
            self.fpx = open(lockname, "wb+")
        except:
            print("Cannot create lock file")

    def waitlock(self):
        if utils_pgdebug > 1:
            print("Waitlock", self.lockname)

        cnt = 0
        while True:
            try:
                buff = self.fpx.read()
                self.fpx.seek(0, os.SEEK_SET)
                self.fpx.write(buff)
                break;
            except:
                if 1: #utils_pgdebug > 1:
                    print("waiting", sys.exc_info())

            if cnt > utils_locktout :
                # Taking too long; break in
                if utils_pgdebug > 1:
                    print("Lock held too long pid =", os.getpid(), cnt, lockname)
                self.unlock()
                break
            cnt += 1
            time.sleep(1)
        # Lock NOW
        fcntl.lockf(self.fpx, fcntl.LOCK_EX)

    def unlock(self):
        fcntl.lockf(self.fpx, fcntl.LOCK_UN)


def truncs(strx, num = 8):

    ''' Truncate a string for printing nicely. Add '..' if truncated'''

    if len(strx) > num:
        strx = strx[:num] + b".."
    return strx

# EOF