#!/usr/bin/env python3

''' Module pydb '''

import  os
import  sys
import  random
import  string
import  getopt

base = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(base, 'pydbase'))

from pydbase import twincore
from pydbase import dbutils

import pyvpacker

import gettext
gettext.bindtextdomain('thisapp', './locale/')
gettext.textdomain('thisapp')
_ = gettext.gettext

#print(sys.prefix)

# pylint: disable=C0321
# pylint: disable=C0103

# ------------------------------------------------------------------------

gl_lockname = "pydbase.main.lock"

# Module variables (pushed to a class)

class _m():
    pgdebug = 0;  verbose = 0
    keyonly = 0;  ncount  = 1
    maxdel = 0xffffffff
    findoff = ""; lcount  = twincore.INT_MAX
    quiet   = 0; writex  = 0;   randx   = 0; skipx   = 0
    offsx   = 0; delx    = 0;   delrx   = 0; delrx2  = 0
    revx   = 0; showdelx = 0;   vacx    = 0; recx    = 0
    integx  = 0; checkf  = 0;   sizex   = 0; findx   = ""
    retrx   = ""; keyx    = ""; datax  = ""
    dkeyx   = ""; dumpx  = 0;   findrec = ""; getrec = 0
    replace = 0 ; recpos = 0;    decode = 0

    deffile = "pydbase.pydb"

VERSION = "1.1.0"
VDATE   = "Fri 26.Apr.2024"

allstr  =    " " + \
                string.ascii_lowercase +  string.ascii_uppercase +  \
                    string.digits

# ------------------------------------------------------------------------

# Return a random string based upon length

def randstr(lenx):

    ''' Deliver a random string for testing '''
    strx = ""
    for aa in range(lenx):
        ridx = random.randint(0, len(allstr)-1)
        rr = allstr[ridx]
        strx += str(rr)
    return strx

pname = os.path.split(__file__)[1]

chelp = '''\
Administer pydbase data.  Version: %s
Usage: %s [options] [newkey newdata]
   -h         Help (this screen)   -|-  -E         Replace record in place
   -V         Print version        -|-  -q         Quiet on, less printing
   -d         Debug level (0-10)   -|-  -v         Increment verbosity level
   -r         Randomize (with -w)  -|-  -w         Write random record(s)
   -z         Dump backwards(s)    -|-  -i         Show deleted record(s)
   -U         Vacuum DB            -|-  -R         Re-index / recover DB
   -I         DB Integrity check   -|-  -c         Set check integrity flag
   -S         Print dbase size     -|-  -m         Dump data to console
   -K         List all, keys only  -|-  -F  subkey Find rec. by subkey
   -O         Decode pyvpacker     -|-  -s  subkey Find file offsets
   -n  num    Num of recs (with -w)-|-  -t  keyval Retrieve by key value
   -o  offs   Get data at offset   -|-  -g         Get records. skip/lim/dec
   -k  keyval Key to save          -|-  -a  str    Data to save
   -y  keyval Get rec offset       -|-  -D  keyval Delete by key skip/rev/lim
   -p  num    Skip number of recs  -|-  -u  recnum Delete at recnum
   -l  lim    Limit get records    -|-  -e  offs   Delete at offset
   -Z  keyval Get record position  -|-  -X  max    Limit recs on delete
   -f  file   DB file for save/retrieve default: 'pydbase.pydb')
The verbosity / debug  level influences the amount of printout presented.\
'''  % (VERSION, pname, )

#   -C  num    Get and print num of records. Skip aware, decode aware

__doc__ = "<pre>" + chelp + "</pre>"

def phelp():

    ''' Program usage information '''
    print(chelp)
    sys.exit(0)

def mainfunc():

    ''' Exercise most / all functions of the twincore library '''

    opts = []
    args = []

    # Old fashioned parsing
    opts_args   = "a:d:e:f:k:l:n:o:s:t:u:x:y:p:D:F:G:X:Z:"
    opts_normal = "mchiVrwzvgqURIK?SECO"
    try:
        opts, args = getopt.getopt(sys.argv[1:],  opts_args + opts_normal )
    except getopt.GetoptError as err:
        print(_("Invalid option(s) on command line:"), err)
        sys.exit(1)

    # Scan twice so verbose shows up early
    for aa in opts:
        if aa[0] == "-h" or aa[0] == "-?":
            phelp()
            sys.exit(1)
        if aa[0] == "-v":
            _m.verbose += 1
        if aa[0] == "-d":
            try:
                _m.pgdebug = int(aa[1])
                #print( sys.argv[0], _("Running at debug level"),  pgdebug)
            except:
                _m.pgdebug = 0

    for aa in opts:
        if aa[0] == "-V":
            core = twincore.TwinCore(_m.deffile, _m.pgdebug)
            print("Script Version:", VERSION)
            print("Engine Version:", twincore.VERSION)
            print("Vers.from  API:", core.version())

            if _m.verbose > 0:
                print("Compiled:", VDATE)
            sys.exit(1)

        # Action flags, one at a time
        if aa[0] == "-z":
            _m.revx = True
        if aa[0] == "-u":
            _m.delrx2 = 1
            _m.delrx = int(aa[1])
        if aa[0] == "-w":
            _m.writex = True
        if aa[0] == "-i":
            _m.showdelx = True
        if aa[0] == "-q":
            _m.quiet = True
        if aa[0] == "-n":
            _m.ncount = int(aa[1])
        if aa[0] == "-t":
            _m.retrx = aa[1]
        if aa[0] == "-l":
            _m.lcount = int(aa[1])
        if aa[0] == "-X":
            _m.maxdel = int(aa[1])
        if aa[0] == "-f":
            _m.deffile = aa[1]
        if aa[0] == "-g":
            _m.getrec = True
        if aa[0] == "-k":
            _m.keyx = aa[1]
        if aa[0] == "-D":
            _m.dkeyx = aa[1]
        if aa[0] == "-a":
            _m.datax = aa[1]
        if aa[0] == "-r":
            _m.randx = True
        if aa[0] == "-U":
            _m.vacx = True
        if aa[0] == "-K":
            _m.keyonly = True
        if aa[0] == "-R":
            _m.recx = True
        if aa[0] == "-p":
            _m.skipx = int(aa[1])
        if aa[0] == "-P":
            _m.replace
        if aa[0] == "-y":
            _m.findx = aa[1]
        if aa[0] == "-o":
            _m.offsx = aa[1]
        if aa[0] == "-e":
            _m.delx = aa[1]
        if aa[0] == "-E":
            _m.replace = True
        if aa[0] == "-c":
            _m.checkf = True
        if aa[0] == "-S":
            _m.sizex = True
        if aa[0] == "-s":
            _m.findoff = aa[1]
        if aa[0] == "-I":
            _m.integx = True
        if aa[0] == "-m":
            _m.dumpx = True
        if aa[0] == "-O":
            _m.decode = True
            global packer
            packer = pyvpacker.packbin()
        if aa[0] == "-F":
            _m.findrec = aa[1]
        if aa[0] == "-Z":
            _m.recpos = aa[1]

    #print("args", len(args), args)

    if len(args) == 1:
        print("Must have zero or two arguments. Use -h for help.")
        sys.exit(1)

    # Set some flags
    twincore.base_quiet     = _m.quiet
    twincore.base_pgdebug   = _m.pgdebug
    twincore.base_pgdebug   = _m.pgdebug

    # Create our database
    core = twincore.TwinCore(_m.deffile, _m.pgdebug)
    core.verbose   = _m.verbose
    core.showdel   = _m.showdelx
    core.integrity = _m.checkf

    # See if we have two arguments, save it as data
    if len(args) == 2:
        #print("args", args)
        curr = core.save_data(args[0], args[1])
        sys.exit(0)

    #print("version", core.get_version())
    #print(dir(core))

    dbsize = core.getdbsize()
    #print("DBsize", dbsize)

    if _m.keyx and _m.datax:
        curr = 0
        if _m.verbose:
            print("adding", _m.keyx, _m.datax)
        for aa in range(_m.ncount):
            curr = core.save_data(_m.keyx, _m.datax, _m.replace)

    elif _m.keyx:
        curr = 0
        data = randstr(random.randint(4, 24))
        if _m.verbose:
            print("adding", _m.keyx, data)
        for aa in range(_m.ncount):
            curr = core.save_data(_m.keyx, data, _m.replace)
        #print("curr", curr)
    elif _m.writex:
        curr = 0
        if _m.randx:
            for aa in range(_m.ncount):
                curr = core.save_data(
                    randstr(random.randint(2, 10)),
                        randstr(random.randint(10, 20)))
        else:
            for aa in range(_m.ncount):
                curr = core.save_data("111 222", "333 444")
        #print("curr", curr)
    elif _m.findx:
        if _m.lcount == 0: _m.lcount = 1
        ddd = core.find_key(_m.findx, _m.lcount)
        print("Found record offsets:", ddd)
    elif _m.keyonly:
        cnt = 0
        if _m.lcount + _m.skipx > dbsize:
            _m.lcount = dbsize - _m.skipx
        for aa in range( _m.lcount-1, _m.skipx-1, -1):
            ddd = core.get_rec(aa)
            print(aa, ddd)
            cnt += 1

    elif _m.getrec:
        getx = 0xffff
        if getx + _m.skipx > dbsize:
            getx = dbsize - _m.skipx
        if getx < 0:
            getx = 0
            #print("Clipping getx to dbsize of", dbsize)
        if _m.skipx < 0:
            _m.skipx = 0
            #print("Clipping to dbsize of", dbsize)

        if _m.verbose:
            print("Getting %d records, skipping %d " % (getx, _m.skipx))

        cnt = 0
        for aa in range(dbsize - 1 - _m.skipx, dbsize - 1 - getx - _m.skipx, -1):
            #_m.skipx, getx + _m.skipx):
            ddd = core.get_rec(aa)
            if not ddd:
                continue
            if cnt >= _m.lcount:
                break
            #print("ddd", ddd)
            if _m.decode:
                try:
                    dec = packer.decode_data(ddd[1])[0]
                    # attempt to do second level
                except:
                    # Cannot decode, Just show record
                    if _m.verbose:
                        print("cannot decode:", sys.exc_info())
                    if _m.pgdebug > 2:
                            dbutils.put_exception("pyvpacker")
                    dec = ddd
                try:
                    if type(dec) == type({}):
                        for aa in dec.keys():
                            if str(dec[aa])[:2] == "pg":
                                dec[aa] = packer.decode_data(dec[aa])[0]
                except:
                    # Cannot decode second level
                    if _m.verbose:
                        print("cannot decode second level:", sys.exc_info())
                    if _m.pgdebug > 2:
                        dbutils.put_exception("second level")
                print(dec)
            else:
                print(ddd)
            cnt += 1

    elif _m.retrx != "":
        ddd = core.retrieve(_m.retrx, _m.ncount)
        if not ddd:
            print("Record:", "'" + _m.retrx + "'", "is not found.")
        else:
            print(ddd)
    elif _m.sizex:
        print("Database size:", core.getdbsize())
    elif _m.offsx:
        ddd = core.get_rec_byoffs(int(_m.offsx))
        print(ddd)
    elif _m.delx:
        ddd = core.del_rec_offs(int(_m.delx))
        print(ddd)
    elif _m.delrx2:
        ddd = core.del_rec(int(_m.delrx))
        print(ddd)
    elif _m.dkeyx:
        ddd = core.del_rec_bykey(_m.dkeyx, _m.maxdel, _m.skipx, _m.revx)
        print("Deleted:", ddd, "records.")
    elif _m.recx:
        ddd = core.reindex()
        print("Reindexed:", ddd, "record(s)")
    elif _m.vacx:
        ddd = core.vacuum()
        print("Vacuumed:", ddd[0], "saved", ddd[1], "record(s)")
    elif _m.integx:
        ddd = core.integrity_check()
        print("Integrity check found good:", ddd[0], "of", ddd[1], "record(s)")
    elif _m.dumpx:
        if _m.revx:
            core.dump_data(_m.lcount, _m.skipx)
        else:
            core.revdump_data(_m.lcount, _m.skipx)
    elif _m.findrec:
        ret = core.findrec(_m.findrec, _m.lcount, _m.skipx)
        if _m.verbose:
            print("Found:", end = "")
        print(ret)
    elif _m.findoff:
        ret = core.findrecoffs(_m.findoff, _m.lcount, _m.skipx)
        if _m.verbose:
            print("Found:", end = "")
        print(ret)
    elif _m.recpos:
        ret = core.findrecpos(_m.recpos, _m.lcount, _m.skipx)
        print(ret)
    else:
        print("Use:", os.path.split(sys.argv[0])[1], "-h to see options and help")

if __name__ == "__main__":

    # Tested with process based lock (OK)
    #twincore.waitlock(gl_lockname)
    mainfunc()
    #twincore.dellock(gl_lockname)

# EOF
