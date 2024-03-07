#!/usr/bin/env python3

'''!
    @mainpage

    # Twinchain

    Block chain layer on top of twincore.

        prev     curr
            record
    |   Time Now    |   Time  Now    |  Time Now     |
    |   hash256   | |    hash256   | |   hash256   | |
    |   Header    | |    Header    | |   Header    | |
    |   Payload   | |    Payload   | |   Payload   | |
    |   Backlink  | |    Backlink  | |   Backlink  | |
                  |----->---|      |---->---|     |------ ...

    The sum of fields saved to the next backlink.

    History:

        0.0.0       Tue 20.Feb.2024     Initial release
        0.0.0       Sun 26.Mar.2023     More features
        1.2.0       Mon 26.Feb.2024     Moved pip home to pydbase/
        1.4.0       Tue 27.Feb.2024     Addedd pgdebug
        1.4.2       Wed 28.Feb.2024     Fixed multiple instances
        1.4.3       Wed 28.Feb.2024     ChainAdm added

'''

import  os, sys, getopt, signal, select, socket, time, struct
import  random, stat, os.path, datetime, threading, uuid
import  struct, io, hashlib

import pyvpacker

base = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(base, '..', 'pydbase'))

from dbutils import *
from twincore import *

version         = "1.4.3"
ProtocolVersion = "1.0"

chain_pgdebug = 0

class DBCheckError(Exception):

    def __init__(self, message):
         self.message = message

class DBLinkError(Exception):

    def __init__(self, message):
         self.message = message

# ------------------------------------------------------------------------

class TwinChain(TwinCore):

    '''
        Derive from database to accomodate block chain.
    '''

    def __init__(self, fname = "pydbchain.pydb", pgdebug = 0, core_verbose = 0):

        global chain_pgdebug

        self.pgdebug = pgdebug
        chain_pgdebug = pgdebug
        set_pgdebug(pgdebug)
        self.core_verbose = core_verbose

        #print("pgdebug:", pgdebug)

        import atexit
        atexit.register(self.cleanup)
        # Upper lock name
        self.ulockname = os.path.splitext(fname)[0] + ".ulock"
        #waitupperlock(self.ulockname)

        super(TwinChain, self).__init__(fname, pgdebug)

        #print("TwinChain.init", self.fname, self.ulockname)

        self.packer = pyvpacker.packbin()
        sss = self.getdbsize()
        if sss == 0:
            payload = {"Initial": "Initial record, do not use."}
            #print("Init anchor record", payload)
            # Here we fake the initial backlink for the anchor record
            self.old_dicx = {}

            dt = datetime.datetime.utcnow()
            fdt = dt.strftime('%a, %d %b %Y %H:%M:%S`')
            self.old_dicx["now"] =  fdt

            # Produce initial data structure
            header = str(uuid.uuid1())
            hh = self._hash_any(payload)

            self.old_dicx["hash256"]  =  hh.hexdigest()
            self.old_dicx["header"]   =  header
            self.old_dicx["payload"]  =  payload
            self.old_dicx["backlink"] =  ""    # empty backlink

            aaa = {}
            self._fill_record(aaa, header, payload)
            encoded = self.packer.encode_data("", aaa)
            self.save_data(header, encoded)

    def cleanup(self):
        #print("cleanup")
        delupperlock(self.ulockname)

    def _hash_any(self, any):

        hh = hashlib.new("sha256");
        if type(any) == type(""):
            hh.update(any)
        if type(any) == type({}):
            sss = self._expand_dict(any)
            hh.update(sss.encode())
        return hh

    def _expand_dict(self, dicx):

        sstr = ""
        for aa in sorted(dicx.keys()):
            sstr += dicx[aa]
        print("sstr", sstr)
        return sstr

    # --------------------------------------------------------------------

    def _fill_record(self, aaa, header, payload):

        aaa["header"] = header
        aaa["payload"] = payload
        aaa["protocol"] = ProtocolVersion

        dt = datetime.datetime.now()
        fdt = dt.strftime('%a, %d %b %Y %H:%M:%S')
        aaa["now"] = fdt
        #self._key_n_data(aaa, "hash32", str(self.hash32(payload)))
        hh = hashlib.new("sha256");


        aaa["hash256"] = hh.hexdigest()

        #dd = hashlib.new("md5"); dd.update(payload)
        #aaa["md5"] =  dd.hexdigest()

        backlink =  self.old_dicx["now"]
        backlink =  self.old_dicx["hash256"]
        backlink += self.old_dicx["header"]
        backlink += self._expand_dict(self.old_dicx["payload"])
        backlink += self.old_dicx["backlink"]

        #print("backlink raw", backlink)

        bl = hashlib.new("sha256"); bl.update(backlink.encode())
        if self.core_verbose > 2:
            print("backlink  ", bl.hexdigest())
        aaa["backlink"] = bl.hexdigest()

        if self.pgdebug > 5:
            print(aaa)

    def get_payload(self, recnum):
        arr = self.get_rec(recnum)
        try:
            decoded = self.packer.decode_data(arr[1])
            #print("decoded", decoded)
        except:
            print("Cannot decode", recnum, sys.exc_info())
            return "Bad record"
        dic = self._get_fields(decoded[0])

        if self.core_verbose > 2:
            print(dic)
        if self.core_verbose > 0:
            print(dic['header'] + " " + dic['now'], dic['payload'])

        return arr[0].decode(), dic['payload']

    def get_payoffs_bykey(self, keyval, maxrec = 1):

        arr = []
        rrr = self.getdbsize()
        for aa in range(rrr -1, -1, -1):
            head = self.get_header(aa)
            if head == keyval:
                arr.append(aa)
                if len(arr) >= maxrec:
                    break
        return arr

    def get_data_bykey(self, keyval, maxrec = 1, check = True):

        arr = []
        rrr = self.getdbsize()
        for aa in range(rrr -1, -1, -1):
            head = self.get_header(aa)
            if head == keyval:
                ch = self.checkdata(aa)
                li = self.linkintegrity(aa)

                if self.core_verbose:
                    print("li", li, "ch", ch)

                if not ch:
                    raise  DBCheckError("Check failed at rec %a" % aa);
                if not li:
                    raise  DBLinkError("Link checl failed at rec %a" % aa);

                pay = self.get_payload(aa)
                arr.append((head, pay))
                if len(arr) >= maxrec:
                    break
        return arr

    def get_header(self, recnum):
        arr = self.get_rec(recnum)
        if self.core_verbose > 1:
            print("arr[0]", arr[0])
            uuu = uuid.UUID(arr[0].decode())
            ddd = str(uuid2date(uuu))
            print("header", arr[0])
        return arr[0].decode()

    def linkintegrity(self, recnum):

        ''' Scan one record an its integrity based on the previous one '''

        if recnum < 1:
            print("Cannot check initial record.")
            return False

        if self.core_verbose > 4:
            print("Checking link ...", recnum)

        arr = self.get_rec(recnum-1)
        try:
            decoded = self.packer.decode_data(arr[1])
        except:
            print("Cannot decode prev:", recnum, sys.exc_info())
            return

        dico = self._get_fields(decoded[0])

        arr2 = self.get_rec(recnum)
        try:
            decoded2 = self.packer.decode_data(arr2[1])
        except:
            print("Cannot decode curr:", recnum, sys.exc_info())
            return

        dic = self._get_fields(decoded2[0])

        backlink =  dico["now"]
        backlink =  dico["hash256"]
        backlink += dico["header"]
        backlink += self._expand_dict(dico["payload"])
        backlink += dico["backlink"]

        #print("backlink raw2", backlink)
        hh = hashlib.new("sha256"); hh.update(backlink.encode())

        if self.core_verbose > 2:
            print("calc      ", hh.hexdigest())
            print("backlink  ", dic['backlink'])

        return hh.hexdigest() == dic['backlink']

    def checkdata(self, recnum):
        arr = self.get_rec(recnum)
        try:
            decoded = self.packer.decode_data(arr[1])
        except:
            print("Cannot decode:", recnum, sys.exc_info())
            return

        dic = self._get_fields(decoded[0])
        hh = self._hash_any(dic['payload'])
        #hh.update(dic['payload'].encode())
        if self.core_verbose > 1:
            print("data", hh.hexdigest())
        if self.core_verbose > 2:
            print("hash", dic['hash256'])
        return hh.hexdigest() == dic['hash256']

    def appendwith(self, header, datax):

        #if type(header) != type(b""):
        #    header = header.encode() #errors='strict')

        #if type(datax) != type(b""):
        #    datax = datax.encode() #errors='strict')

        if self.pgdebug > 1:
            print("Appendwith", header, datax)

        if self.core_verbose > 0:
            print("Appendwith", header, datax)

        try:
            uuu = uuid.UUID(header)
        except:
            if self.core_verbose:
                print("Header override must be a valid UUID string.")
            raise ValueError("Header override must be a valid UUID string.")

        waitupperlock(self.ulockname)

        self.old_dicx = {}
        # Get last data from db
        sss = self.getdbsize()
        #print("sss", sss)

        if not sss:
            raise ValueError("Invalid database, must have at least one record.")

        ooo = self.get_rec(sss-1)
        if self.pgdebug > 2:
            print("ooo", ooo)

        decoded = self.packer.decode_data(ooo[1])
        if self.pgdebug > 4:
            print("decoded", decoded)

        self.old_dicx = self._get_fields(decoded[0])
        if self.pgdebug > 3:
            print(self.old_dicx)

        #print("old_fff", self.old_dicx["hash256"])
        #print("old_time", self.old_dicx["now"])

        aaa = {}
        self._fill_record(aaa, header, datax)

        encoded = self.packer.encode_data("", aaa)
        if self.pgdebug > 2:
            print("encoded", encoded)

        #print("save", header, "-", encoded)

        #print("bbb", self.getdbsize())
        self.save_data(header, encoded)
        #print("eee", self.getdbsize())
        #if self.pgdebug > 5:

        if self.core_verbose > 1:
            bbb = self.packer.decode_data(encoded)
            print("Rec", bbb[0])

        if self.pgdebug:
            bbb = self.packer.decode_data(encoded)
            self.dump_rec(bbb[0])

        delupperlock(self.ulockname)
        return True

    def append(self, datax):

        if self.core_verbose > 0:
            print("Append", datax)

        #if type(datax) != b"":
        #    datax = datax.encode() #errors='strict')

        self.old_dicx = {}
        # Get last data from db
        sss = self.getdbsize()
        #print("sss", sss)

        if not sss:
            raise ValueError("Invalid database, must have at least one record.")

        # Produce header  structure
        uuu = uuid.uuid1()
        #print("uuid date",uuid2date(uuu))
        header = str(uuu)
        uuuu = uuid.UUID(header)
        #print("uuid date2", header, uuid2date(uuuu))
        ret = self.appendwith(header, datax)
        return ret

    def dump_rec(self, bbb):
        for aa in range(len(bbb)//2):
            print(pad(bbb[2*aa]), "=", bbb[2*aa+1])

    def _get_fields(self, bbb):
        if type(bbb) == type({}):
            dicx = bbb
        else:
            dicx = {}
            for aa in range(len(bbb)//2):
                dicx[bbb[2*aa]] = bbb[2*aa+1]
            if self.pgdebug > 7:
                print("dicx", dicx)
        return dicx

# EOF
