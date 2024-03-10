#!/usr/bin/env python3

import  os, sys, getopt, signal, select, socket, time, struct
import  random, stat, os.path, datetime, threading, warnings
import  string, hashlib, uuid

import pyvpacker

import gettext
gettext.bindtextdomain('thisapp', './locale/')
gettext.textdomain('thisapp')
_ = gettext.gettext

from pydbase import twinchain
from pydbase import dbutils

version = "0.0.1"

#print("hashes", hashlib.algorithms_guaranteed)

# Module variables (pushed to a class)

class _c():
    deffile = "pydbchain.pydb"
    maxx    = 0xffffffff
    lcount  = twinchain.INT_MAX
    quiet   = 0;    writex  = 0
    randx   = 0;    skipx   = 0
    offsx   = 0;    delx    = 0
    delrx   = 0;    delrx2  = 0
    backx   = 0;    sdelx   = 0
    vacx    = 0;    recx    = 0
    integx  = 0;    checkx  = 0
    sizex   = 0;    findx   = ""
    pgdebug = 0;    verbose = 0
    keyonly = 0;    ncount  = 1
    skipcnt = 0;    append  = 0
    retrx   = "";   getit  = ""
    keyx    = "";   datax  = ""
    dkeyx   = "";   dumpx  = 0
    findrec = "";   getrec = -1
    datex = 0   ;   cntx = 1
    headx = ""  ;   gethead = -1
    getby = ""  ;   getoffs = ""

def help():

    ''' Deliver program usage information '''

    print("Usage: %s [options]" % os.path.split(sys.argv[0])[1])
    print("   Options: -a  data   append data to the end of chain")
    print("            -g recnum  get record")
    print("            -k reckey  get record by key/header")
    print("            -G recnum  get record offset by key")
    print("            -r recnum  get record header")
    print("            -n         append / show / get number of records")
    print("            -e         override header (checked for UUID)")
    print("            -t         print record's UUID date)")
    print("            -s         skip count")
    print("            -x         max record count to list")
    print("            -m         dump chain data")
    print("            -c         check data integrity")
    print("            -i         check link integrity")
    print("            -S         get db size")
    print("            -v         increase verbosity")
    print("            -h         help (this screen)")

def mainfunc():

    ''' Exersize funtions of the twinchain library. '''

    opts = []; args = []

    # Old fashioned parsing
    opts_args   = "K:a:d:e:f:g:k:l:n:o:r:s:u:x:y:p:D:F:G:d:g:k:"
    opts_normal = "mchiVwzvqURIK?St"
    try:
        opts, args = getopt.getopt(sys.argv[1:],  opts_normal + opts_args)
    except getopt.GetoptError as err:
        print(_("Invalid option(s) on command line:"), err)
        sys.exit(1)

    # Scan twice so verbose shows up early
    for aa in opts:
        if aa[0] == "-h" or aa[0] == "-?":
            help(); exit(1)

        if aa[0] == "-V":
            print("Script Version:", version);
            print("Engine Version:", twincore.version);
            exit(0)

        if aa[0] == "-f":
            _c.deffile = aa[1]

        if aa[0] == "-a":
            _c.append = aa[1]

        if aa[0] == "-n":
            _c.cntx = int(aa[1])

        if aa[0] == "-g":
            _c.getrec = int(aa[1])

        if aa[0] == "-k":
            _c.getby = aa[1]

        if aa[0] == "-G":
            _c.getoffs = aa[1]

        if aa[0] == "-x":
            _c.maxx = int(aa[1])

        if aa[0] == "-r":
            _c.gethead = int(aa[1])

        if aa[0] == "-s":
            _c.skipcnt = int(aa[1])

        if aa[0] == "-m":
            _c.dumpx = True

        if aa[0] == "-e":
            _c.headx = aa[1]

        if aa[0] == "-t":
            _c.datex = True

        if aa[0] == "-S":
            _c.sizex = True

        if aa[0] == "-v":
            _c.verbose += 1

        if aa[0] == "-d":
            try:
                _c.pgdebug = int(aa[1])
            except:
                print("Warn: debug level needs to be numeric.")

        if aa[0] == "-c":
            _c.checkx = True

        if aa[0] == "-i":
            _c.integx = True

    execfunc()

    #print("Use: pychain.py -h to see options and help")

def execfunc():

    ''' Execute individual function from command line '''

    # Create our database
    core = twinchain.TwinChain(_c.deffile, _c.pgdebug, _c.verbose)

    if _c.integx:
        #print("Integrity", _c.integx)
        errx = False; cnt = []
        sss = core.getdbsize()
        # Remember record zero is the anchor
        for aa in range(1, sss):
            ppp = core.linkintegrity(aa)
            if _c.verbose:
                print(aa, ppp)
            if not ppp: errx = True; cnt.append(aa)
        if errx:
            print("error on rec", cnt)
        else:
            print("DB integrity on %d rec checks out OK" % sss)

    elif _c.getrec >= 0:
        sss = core.getdbsize()
        if _c.getrec > sss:
            print("Cannot get past end of file.")
            sys.exit()
        if _c.getrec + _c.cntx > sss:
            _c.cntx = sss - _c.getrec
        for aaa in range(_c.cntx):
            ppp = core.get_payload(_c.getrec + aaa)
            print(ppp)

    elif _c.gethead >= 0:
        sss = core.getdbsize()
        if _c.gethead > sss:
            print("Cannot get past end of file.")
            sys.exit()
        for aaa in range(_c.cntx):
            ppp = core.get_header(_c.gethead + aaa)
            print(ppp)

    elif _c.checkx:
        #print("Checking", _c.checkx)
        errx = False; cnt = -1
        sss = core.getdbsize()
        for aa in range(sss):
            ppp = core.checkdata(aa)
            if _c.verbose:
                print(aa, ppp)
            if not ppp: errx = True; cnt = aa
        if errx:
            print("error on rec", cnt)
        else:
            print("DB checks out OK")

    elif _c.dumpx:
        #print("Dumping", _c.dumpx)
        sss = core.getdbsize()
        cnt = _c.skipcnt
        if cnt >= sss:
            print("Passed EOF")
            sys.exit(0)
        end = min(sss, _c.maxx + cnt)
        while True:
            if cnt >= end:
                break
            hhh = core.get_header(cnt)
            ppp = core.get_payload(cnt)
            ddd = ""
            if  _c.datex:
                ddd = dbutils.uuid2date(uuid.UUID(ppp[0]))
            print(cnt, hhh, ddd, ppp)
            cnt = cnt + 1

    elif _c.append:
        #print("Appending", _c.append)
        dicx = {}; arrx = []
        arrx = _c.append.split()
        if len(arrx) % 2:
            dicx['unkown'] = _c.append
        else:
            for aa in arrx:
                arrz = aa.split(":")
                if len(arrz) == 1:
                    arrx = aa
                else:
                    dicx[arrz[0]] = arrz[1]
        # Array or dic?
        if len(arrx):
            dicx =  arrx
        #print("Appending", dicx)
        for aaa in range(_c.cntx):
            if _c.headx:
                core.appendwith(_c.headx, dicx)
            else:
                core.append(dicx)

    elif _c.getby:
        #print("get bykey getby")
        #rec = core.retrieve(_c.getby, _c.ncount)
        rec = core.get_data_bykey(_c.getby, _c.ncount)
        if not rec:
            print("Record:", "'" + _c.getby + "'", "not found")
        else:
            print(rec)

    elif _c.sizex:
        print("Database size:", core.getdbsize())
    elif _c.getoffs:
        arr = core.get_payoffs_bykey(_c.getoffs, _c.cntx)
        print(arr)

    else:
        print("Use:", os.path.split(sys.argv[0])[1], "-h for info on usage.")

# ------------------------------------------------------------------------

if __name__ == "__main__":

    mainfunc()
    #print(type(b"") == bytes)

# EOF
