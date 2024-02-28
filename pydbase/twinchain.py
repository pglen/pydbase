#!/usr/bin/env python3

'''!
    @mainpage

    # Twinchain

    Block chain layer on top of twincore.

        prev     curr
            record
   |    Now        |     Now        |     Now       |
   |   hash32      |    hash32      |    hash32     |
   |   hash256   | |    hash256   | |   hash256   | |
   |   Header    | |    Header    | |   Header    | |
   |   Payload   | |    Payload   | |   Payload   | |
   |   Backlink  | |    Backlink  | |   Backlink  | |
                 |----->---|      |---->---|     |------ ...

    The sum of fields saved to the next backlink.

    backlink

    History:

        Sun 26.Mar.2023   --  Initial

'''

import  os, sys, getopt, signal, select, socket, time, struct
import  random, stat, os.path, datetime, threading, uuid
import  struct, io, hashlib

import pyvpacker

base = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(base, '..', 'pydbase'))

from twincore import *

version = "1.4.1 dev"
protocol = "1.0"

# ------------------------------------------------------------------------
# Get date out of UUID

def _uuid2date(uuu):

    UUID_EPOCH = 0x01b21dd213814000
    dd = datetime.datetime.fromtimestamp(\
                    (uuu.time - UUID_EPOCH)*100/1e9)
    print(dd.timestamp())

    return dd

def _uuid2timestamp(uuu):

    UUID_EPOCH = 0x01b21dd213814000
    dd = datetime.datetime.fromtimestamp(\
                    (uuu.time - UUID_EPOCH)*100/1e9)
    return dd.timestamp()

def _pad(strx, lenx=8):
    ttt = len(strx)
    if ttt >= lenx:
        return strx
    padx = " " * (lenx-ttt)
    return strx + padx

# ------------------------------------------------------------------------

class TwinChain(TwinCore):

    '''
        Derive from database to accomodate block chain.
    '''

    def __init__(self, fname = "pydbchain.pydb", pgdebug = 0, core_verbose = 0):

        super(TwinChain, self).__init__(fname)
        self.pgdebug = pgdebug
        self.core_verbose = core_verbose

        #print("TwinChain.init", self.fname)
        self.packer = pyvpacker.packbin()
        sss = self.getdbsize()
        if sss == 0:
            payload = b"Initial record, do not use."
            #print("Init anchor record", payload)
            # Here we fake the initial backlink for the anchor record
            self.old_dicx = {}

            dt = datetime.datetime.utcnow()
            fdt = dt.strftime('%a, %d %b %Y %H:%M:%S`')
            self.old_dicx["now"] =  fdt

            # Produce initial data structure
            header = str(uuid.uuid1())
            aaa = []

            hh = hashlib.new("sha256"); hh.update(payload)
            self.old_dicx["hash256"]  =  hh.hexdigest()
            self.old_dicx["header"]   =  header
            self.old_dicx["payload"]  =  payload
            self.old_dicx["backlink"] =  ""    # empty backlink

            self._fill_record(aaa, header, payload)
            encoded = self.packer.encode_data("", aaa)
            self.save_data(header, encoded)

    def  _key_n_data(self, arrx, keyx, strx):
        arrx.append(keyx)
        arrx.append(strx)

    # --------------------------------------------------------------------

    def _fill_record(self, aaa, header, payload):

        self._key_n_data(aaa, "header", header)
        self._key_n_data(aaa, "protocol", protocol)

        dt = datetime.datetime.now()
        fdt = dt.strftime('%a, %d %b %Y %H:%M:%S')
        self._key_n_data(aaa, "now", fdt)
        self._key_n_data(aaa, "payload", payload)
        self._key_n_data(aaa, "hash32", str(self.hash32(payload)))
        hh = hashlib.new("sha256"); hh.update(payload)
        self.new_fff = hh.hexdigest()
        self._key_n_data(aaa, "hash256", self.new_fff)

        dd = hashlib.new("md5"); dd.update(payload)
        self._key_n_data(aaa, "md5", dd.hexdigest())

        backlink =  self.old_dicx["hash256"]
        backlink += self.old_dicx["header"]
        backlink += self.old_dicx["payload"].decode()
        backlink += self.old_dicx["backlink"]
        #backlink += self.new_fff

        #print("backlink raw", backlink)

        bl = hashlib.new("sha256"); bl.update(backlink.encode())

        if self.core_verbose > 2:
            print("backlink  ", bl.hexdigest())

        self._key_n_data(aaa, "backlink", bl.hexdigest())

        if self.pgdebug > 5:
            print(aaa)
        #self.old_dicx = {}

    def get_payload(self, recnum):
        arr = self.get_rec(recnum)
        decoded = self.packer.decode_data(arr[1])
        dic = self.get_fields(decoded[0])
        if self.core_verbose > 2:
            return dic
        if self.core_verbose > 1:
            uuu = uuid.UUID(dic['header'])
            ddd = str(_uuid2date(uuu))
            return dic['header'] + " " + dic['now'] + " -- " + ddd + " -- " \
                                + dic['payload'].decode()
        if self.core_verbose > 0:
            return dic['header'] + " " + dic['now'] + " " + dic['payload'].decode()

        return arr[0].decode(), dic['payload']

    def linkintegrity(self, recnum):

        ''' Scan one record an its integrity based on the previous one '''

        if recnum < 1:
            print("Cannot check initial record.")
            return False

        if self.core_verbose > 4:
            print("Checking link ...", recnum)

        arr = self.get_rec(recnum-1)
        decoded = self.packer.decode_data(arr[1])
        dico = self.get_fields(decoded[0])

        arr2 = self.get_rec(recnum)
        decoded2 = self.packer.decode_data(arr2[1])
        dic = self.get_fields(decoded2[0])

        backlink =  dico["hash256"]
        backlink += dico["header"]
        backlink += dico["payload"].decode()
        backlink += dico["backlink"]

        print("backlink raw2", backlink)
        hh = hashlib.new("sha256"); hh.update(backlink.encode())

        if self.core_verbose > 2:
            print("calc      ", hh.hexdigest())
            print("backlink  ", dic['backlink'])

        return hh.hexdigest() == dic['backlink']

    def checkdata(self, recnum):
        arr = self.get_rec(recnum)
        decoded = self.packer.decode_data(arr[1])
        dic = self.get_fields(decoded[0])

        hh = hashlib.new("sha256");
        hh.update(dic['payload'])
        #hh.update(dic['payload'].encode())
        if self.core_verbose > 1:
            print("data", hh.hexdigest())
        if self.core_verbose > 2:
            print("hash", dic['hash256'])
        return hh.hexdigest() == dic['hash256']

    def append(self, datax):

        if self.core_verbose > 0:
            print("Append", datax)

        if type(datax) == str:
            datax = datax.encode() #errors='strict')

        self.old_dicx = {}
        # Get last data from db
        sss = self.getdbsize()
        #print("sss", sss)

        if not sss:
            raise Valuerror("Invalid database, must be at least one record")

        ooo = self.get_rec(sss-1)
        #print("ooo", ooo)
        decoded = self.packer.decode_data(ooo[1])
        self.old_dicx = self.get_fields(decoded[0])
        if self.pgdebug > 3:
            print(self.old_dicx)

        #print("old_fff", self.old_dicx["hash256"])
        #print("old_time", self.old_dicx["now"])

        # Produce data structure
        uuu = uuid.uuid1()
        #print(_uuid2date(uuu))
        header = str(uuu)
        aaa = []
        self._fill_record(aaa, header, datax)
        encoded = self.packer.encode_data("", aaa)
        if self.pgdebug > 2:
            print(encoded)
        self.save_data(header, encoded)

        if self.core_verbose > 1:
            bbb = self.packer.decode_data(encoded)
            print("Rec", bbb[0])

        if self.pgdebug:
            bbb = self.packer.decode_data(encoded)
            self.dump_rec(bbb[0])

    def dump_rec(self, bbb):
        for aa in range(len(bbb)//2):
            print(_pad(bbb[2*aa]), "=", bbb[2*aa+1])

    def get_fields(self, bbb):
        dicx = {}
        for aa in range(len(bbb)//2):
            dicx[bbb[2*aa]] = bbb[2*aa+1]

        #print("dicx", dicx)
        return dicx

    def __del__(self):
        ''' Override for now '''
        pass

# EOF
