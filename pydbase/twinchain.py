#!/usr/bin/env python3

'''
    <pre>

 Block chain layer on top of twincore.

    |   Time Now    |   Time  Now    |  Time Now     |
    |   hash256   | |    hash256   | |   hash256   | |
    |   Header    | |    Header    | |   Header    | |
    |   Payload   | |    Payload   | |   Payload   | |
    |   Backlink  | |    Backlink  | |   Backlink  | |
                  |----->---|      |---->---|     |------

    The sum of fields saved to the next backlink.

    History:

    1.1         Tue 20.Feb.2024     Initial release
    1.2.0       Mon 26.Feb.2024     Moved pip home to pydbase/
    1.4.0       Tue 27.Feb.2024     Addedd pgdebug
    1.4.2       Wed 28.Feb.2024     Fixed multiple instances
    1.4.3       Wed 28.Feb.2024     ChainAdm added
    1.4.4       Fri 01.Mar.2024     Tests for chain functions
    1.4.5       Fri 01.Mar.2024     Misc fixes
    1.4.6       Mon 04.Mar.2024     Vacuum count on vacuumed records
    1.4.7       Tue 05.Mar.2024     In place record update
    1.4.8       Sat 09.Mar.2024     Added new locking mechanism
    1.4.9       Mon 01.Apr.2024     Updated to run on MSYS2, new locking
    1.5.0       Tue 02.Apr.2024     Cleaned, pip upload
    1.5.1       Wed 10.Apr.2024     Dangling lock .. fixed

    </pre>
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

# Exceptions for bad records

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

    def __init__(self, fname = "pydbchain.pydb", pgdebug = 0, verbose = 0):

        self.chain_verbose = verbose

        # Upper lock name
        ulockname = os.path.splitext(fname)[0] + ".ulock"
        self.ulock = FileLock(ulockname)
        self.ulock.waitlock()    #(self.ulockname)

        super(TwinChain, self).__init__(fname, pgdebug)

        self.packer = pyvpacker.packbin()

        sss = self.getdbsize()
        '''if sss == 0:
            # Produce initial data structure
            # This is the wron place to produce it, as the chain has no
            # knowledge of the actual structure ... we provide minimum here
            header = str(uuid.uuid1())
            dt = datetime.datetime.utcnow()
            fdt = dt.strftime('%a, %d %b %Y %H:%M:%S`')

            payload = {"Initial": "Initial record, do not use.",
                            "Default" : 'None', "header": header}

            #payload2 = {"header": header, "payload" : payload}

            # Here we fake the initial backlink for the anchor record
            old_dicx = {}
            old_dicx["now"] =  fdt
            old_dicx["hash256"]  =  self._hash_any(payload).hexdigest()
            old_dicx["header"]   =  header
            old_dicx["payload"]  =  payload
            old_dicx["backlink"] =  ""

            #print("old_dicx:", self.old_dicx)

            aaa = self._fill_record(header, payload, old_dicx)
            #print("aaa:", aaa)
            encoded = self.packer.encode_data("", [aaa])
            #print("encoded:", encoded)

            self.save_data(header, encoded)
        '''

        self.ulock.unlock() #self.ulockname)

    def _hashtohex(self, varx):

        if type(varx) == type(""):
            varx = varx.encode()

        hh = hashlib.new("sha256");
        hh.update(varx)
        return hh.hexdigest()

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
        if type(dicx) == type({}):
            for aa in sorted(dicx.keys()):
                sstr += aa + ":" + dicx[aa]
        if type(dicx) == type([]):
            for aa in dicx:
                sstr += aa
        if type(dicx) == type(""):
            sstr = dicx
        if type(dicx) == type(b""):
            sstr = dicx

        #print("sstr", sstr)
        return sstr

    def _build_sumstr(self, aaa):

        sumstr  = aaa.get('now', "")
        sumstr += aaa.get('header', "")
        sumstr += self._expand_dict(aaa.get('payload', ""))
        #print("raw sumstr", sumstr)
        return sumstr

    def _build_backlink(self, dicold):

        backlink  =  dicold.get("now", "")
        backlink +=  dicold.get("hash256", "")
        backlink += dicold.get("header", "")
        backlink += self._expand_dict(dicold.get("payload", ""))
        backlink += dicold.get("backlink", "")
        #print("raw backlink", backlink)
        return backlink

    # --------------------------------------------------------------------

    def _fill_record(self, header, payload, old_dict):

        aaa = {}
        aaa["header"] = header
        aaa["payload"] = payload
        aaa["protocol"] = ProtocolVersion

        dt = datetime.datetime.now()
        fdt = dt.strftime('%a, %d %b %Y %H:%M:%S')
        aaa["now"] = fdt
        #self._key_n_data(aaa, "hash32", str(self.hash32(payload)))

        sumstr = self._build_sumstr(aaa)
        aaa["hash256"] = self._hashtohex(sumstr)

        backlink = self._build_backlink(old_dict)
        aaa["backlink"] = self._hashtohex(backlink)

        return aaa

    def get_payload(self, recnum):

        ''' Return the payload on record number '''

        arr = self.get_rec(recnum)
        if not arr:
            return []
        try:
            decoded = self.packer.decode_data(arr[1])
            #print("decoded", decoded)
        except:
            print("Cannot decode record at", recnum, recnum, sys.exc_info())
            raise
        dic = self._get_fields(decoded[0])

        if self.chain_verbose > 2:
            print(dic)
        if self.chain_verbose > 0:
            print(dic['header'] + " " + dic['now'], dic['payload'])

        return arr[0].decode(), dic['payload']

    def get_payoffs_bykey(self, keyval, maxrec = 1):
        " get payload offset by key"
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

        ''' Get data by key value. Searches the database from the back so lastly
            entered data is presented.

            Input:

                keyval    :    value to search for
                maxrec    :    maximum number of records
                check     :    check as found. Raises exception

            Returns:

                data array matching criteria.

        '''
        arr = []
        rrr = self.getdbsize()
        for aa in range(rrr -1, -1, -1):
            head = self.get_header(aa)
            if head == keyval:
                ch = self.checkdata(aa)
                li = self.linkintegrity(aa)

                if self.chain_verbose:
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

        ''' Get the header of record. '''

        if self.pgdebug > 5:
            print("get_header()", recnum)
        arr = self.get_rec(recnum)
        if not arr:
            if self.pgdebug > 5:
                print("get_header(): empty/deleted record", recnum)

            if self.chain_verbose > 1:
                print("get_header(): empty/deleted record", recnum)
            return []

        if self.chain_verbose > 1:
            print("arr", arr)
            uuu = uuid.UUID(arr[0].decode())
            ddd = str(uuid2date(uuu))
            print("header", arr[0])
        return arr[0].decode()

    def linkintegrity(self, recnum):

        ''' Scan one record an its integrity based on the previous one '''

        if recnum < 1:
            if self.chain_verbose:
                print("Cannot check initial record.")
            return True

        if self.chain_verbose > 4:
            print("Checking link ...", recnum)

        arr = self.get_rec(recnum-1)
        try:
            decoded = self.packer.decode_data(arr[1])
        except:
            print("Cannot decode prev:", recnum, sys.exc_info())
            return
        dicold = self._get_fields(decoded[0])
        arr2 = self.get_rec(recnum)
        try:
            decoded2 = self.packer.decode_data(arr2[1])
        except:
            if self.chain_verbose > 2:
                print("Cannot decode curr:", recnum, sys.exc_info())
            return
        dic = self._get_fields(decoded2[0])
        backlink = self._build_backlink(dicold)
        hhh = self._hashtohex(backlink)
        if self.chain_verbose > 2:
            print("calc      ", hhh)
            print("backlink  ", dic['backlink'])
        return hhh == dic['backlink']

    def checkdata(self, recnum):

        ''' Integrity check of record. '''

        arr = self.get_rec(recnum)
        try:
            decoded = self.packer.decode_data(arr[1])
        except:
            if self.chain_verbose > 2:
                print("Cannot decode:", recnum, sys.exc_info())
            return

        aaa = self._get_fields(decoded[0])
        sumstr = self._build_sumstr(aaa)
        hhh = self._hashtohex(sumstr)
        if self.chain_verbose > 1:
            print("data", hhh)
        if self.chain_verbose > 2:
            print("hash", aaa['hash256'])
        return hhh == aaa['hash256']

    def appendwith(self, header, datax):

        ''' Append data and header to the end of database '''

        #if type(header) != type(b""):
        #    header = header.encode() #errors='strict')

        #if type(datax) != type(b""):
        #    datax = datax.encode() #errors='strict')

        if self.chain_verbose > 0:
            print("Appendwith", header, datax)

        self.ulock.waitlock()    #self.ulockname)

        try:
            uuu = uuid.UUID(header)
        except:
            if self.chain_verbose:
                print("Header override must be a valid UUID string.")

            self.ulock.unlock() #self.ulockname)
            raise ValueError("Header override must be a valid UUID string.")

        old_dicx = {}
        # Get last data from db
        sss = self.getdbsize()
        #print("sss", sss)

        # We fake an empty set ... checking against an empty set is a valid OP
        if not sss:
            #raise ValueError("Invalid database, must have at least one record.")
            ddd = self.packer.encode_data("", {"blank": 0, })
            ooo = [0, ddd,]
        else:
            ooo = self.get_rec(sss-1)

        if self.pgdebug > 5:
            print("decoding", ooo)

        decoded = self.packer.decode_data(ooo[1])
        old_dicx = self._get_fields(decoded[0])

        #print("old_fff", old_dicx["hash256"])
        #print("old_time", old_dicx["now"])

        aaa = self._fill_record(header, datax, old_dicx)
        encoded = self.packer.encode_data("", aaa)

        #print("save", header, "-", encoded)
        #print("bbb", self.getdbsize())
        self.save_data(header, encoded)
        #print("eee", self.getdbsize())

        if self.chain_verbose > 1:
            bbb = self.packer.decode_data(encoded)
            print("Rec", bbb[0])

        self.ulock.unlock() #self.ulockname)
        return True

    def append(self, datax):

        ''' Append data to the end of database '''

        if self.chain_verbose > 0:
            print("Append", datax)

        # Get last data from db
        #sss = self.getdbsize()
        #if not sss:
        #    #raise ValueError("Invalid database, must have at least one record.")
        #    pass

        # Produce header  structure
        uuu = uuid.uuid1()
        #print("uuid date",uuid2date(uuu))
        header = str(uuu)
        uuuu = uuid.UUID(header)
        #print("uuid date2", header, uuid2date(uuuu))
        ret = self.appendwith(header, datax)
        return ret

    def dump_rec(self, bbb):

        ''' Dump one record to console '''

        for aa in range(len(bbb)//2):
            print(pad(bbb[2*aa]), "=", bbb[2*aa+1])

    def _get_fields(self, bbb):
        if type(bbb) == type({}):
            dicx = bbb
        else:
            dicx = {}
            for aa in range(len(bbb)//2):
                dicx[bbb[2*aa]] = bbb[2*aa+1]
        return dicx

# EOF
