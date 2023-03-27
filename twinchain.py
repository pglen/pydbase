#!/usr/bin/env python3

'''!
    @mainpage

    # Twinchain

    Block chain layer on top of twincore

    History:

        Sun 26.Mar.2023   --  Initial

'''

import  os, sys, getopt, signal, select, socket, time, struct
import  random, stat, os.path, datetime, threading, uuid
import  struct, io, hashlib

from twincore import *
import pypacker

version = "1.0 dev"

# NamedAtomicLock -- did not work here

# ------------------------------------------------------------------------

class TwinChain(TwinCore):

    '''

    '''

    def __init__(self, fname = "pydbchain.pydb"):

        #super(TwinCore, self).__init__(fname)
        # Fuck; this one finally worked
        super().__init__(fname)
        #print("TwinChain.init", self.fname)
        self.packer = pypacker.packbin()

        pass

    def  _key_n_data(self, arrx, keyx, strx):
        arrx.append(keyx)
        arrx.append(strx)

    def _pad(self, strx, lenx=8):
        ttt = len(strx)
        if ttt >= lenx:
            return strx
        padx = " " * (lenx-ttt)
        return strx + padx

    def append(self, datax):

        #print("Appending data", data)
        if type(datax) == str:
            datax = datax.encode(errors='strict')

        self.old_fff = ""
        # Get last data from db
        sss = self.getdbsize()
        #print("sss", sss)
        if sss:
            ooo = self.get_rec(sss-1)
            #print("ooo", ooo)
            decoded = self.packer.decode_data(ooo[1])
            #self.dump_rec(decoded[0])
            self.old_fff = self.get_field(decoded[0], "hash256")
            self.old_time = self.get_field(decoded[0], "now")
            print("old_fff", self.old_fff)
            print("old_time", self.old_time)

        # Produce data structure
        aaa = []
        header = str(uuid.uuid4())
        self._key_n_data(aaa, "header", header)
        dt = datetime.datetime.utcnow()
        fdt = dt.strftime('%a, %d %b %Y %H:%M:%S GMT')
        self._key_n_data(aaa, "now", fdt)
        self._key_n_data(aaa, "payload", datax)
        self._key_n_data(aaa, "hash32", str(self.hash32(datax)))

        hh = hashlib.new("sha256")
        hh.update(datax)
        self.new_fff = hh.hexdigest()
        self._key_n_data(aaa, "hash256", self.new_fff)

        dd = hashlib.new("md5")
        dd.update(datax)
        self._key_n_data(aaa, "md5", dd.hexdigest())

        #print("old_fff", self.old_fff, "new_fff", self.new_fff)
        backlink = (self.old_fff + self.new_fff + fdt).encode()
        hh.update(backlink)
        self.new_fff = hh.hexdigest()
        self._key_n_data(aaa, "backlink", hh.hexdigest())

        encoded = self.packer.encode_data("", aaa)
        #print(encoded)

        self.save_data(header, encoded)

        bbb = self.packer.decode_data(encoded)
        #print(bbb[0])
        self.dump_rec(bbb[0])

    def dump_rec(self, bbb):
        for aa in range(len(bbb)//2):
            print(self._pad(bbb[2*aa]), "=", bbb[2*aa+1])

    def get_field(self, bbb, field):
        for aa in range(len(bbb)//2):
            #print("bbb", bbb[2*aa], bbb[2*aa+1])
            if bbb[2*aa] == field:
                return bbb[2*aa+1]

    def __del__(self):
        ''' Override for now '''
        pass


# EOF
