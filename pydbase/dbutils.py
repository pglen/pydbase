#!/usr/bin/env python3

import datetime, time, traceback, multiprocessing

import sys, os

try:
    import fcntl
except:
    fcntl = None

utils_pgdebug  = 0
utils_locktout = 5

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

    ''' A working file lock in Linux and Windows '''

    def __init__(self, lockname):

        ''' Create the lock file, else just remember the name '''

        if not lockname:
            raise ValuError("Must specify lockfile")
        self.lockname = lockname

        if utils_pgdebug:
            print("lockname init", self.lockname)

        if fcntl:
            try:
                self.fpx = open(lockname, "wb")
            except:
                if utils_pgdebug > 1:
                    print("Cannot create lock file")

                raise ValueError("Cannot create lock file")

    def waitlock(self):
        if utils_pgdebug > 1:
            print("Waitlock", self.lockname)
        if fcntl:
            cnt2 = 0
            while True:
                try:
                    fcntl.flock(self.fpx, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    break
                except:
                    if utils_pgdebug:
                        print("waiting in fcntl", self.lockname,
                                            os.getpid()) #sys.exc_info())

                cnt2 += 1
                time.sleep(1)
                if cnt2 > utils_locktout:
                    # Taking too long; break in
                    if utils_pgdebug:
                        print("Lock held too long",
                                            os.getpid(), self.lockname)
                    self.unlock()
                    break
        else:
            cnt = 0
            while True:
                try:
                    if os.path.exists(self.lockname):
                        if utils_pgdebug:
                           print("Waiting ... ", self.lockname)
                        pass
                    else:
                        fp = open(self.lockname, "wb")
                        fp.write(str(os.getpid()).encode())
                        fp.close()
                        break
                except:
                    if utils_pgdebug:
                        print("locked",  self.lockname, cnt, sys.exc_info())
                    pass
                time.sleep(1)
                cnt += 1
                if cnt > utils_locktout:
                    if utils_pgdebug:
                        print("breaking lock", self.lockname)
                    break

    def unlock(self):

        #print("Unlock", self.lockname)

        if fcntl:
            try:
                fcntl.flock(self.fpx, fcntl.LOCK_UN | fcntl.LOCK_NB)
            except:
                pass
        else:
            try:
                os.remove(self.lockname)
            except:
                pass
                if utils_pgdebug:
                    print("unlock", self.lockname, sys.exc_info())

    def __del__(self):

        #print("__del__ lock", self.lockname)
        try:
            if fcntl:
                # Do not remove, others may have locked it ...
                # ... but close our handle
                fcntl.flock(self.fpx, fcntl.LOCK_UN | fcntl.LOCK_NB)
                self.fpx.close()
                pass

            # Always remove file
            try:
                os.remove(self.lockname)
            except:
                pass
                #print("cannot delete lock", self.lockname, sys.exc_info())
        except:

            if utils_pgdebug:
                print("exc on del (ignored)", self.lockname, sys.exc_info())
            pass

def truncs(strx, num = 8):

    ''' Truncate a string for printing nicely. Add '..' if truncated'''

    if len(strx) > num:
        strx = strx[:num] + b".."
    return strx

# EOF