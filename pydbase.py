#!/usr/bin/env python3

import  os, sys, getopt, signal, select, socket, time, struct
import  random, stat, os.path, datetime, threading, warnings
import string

import gettext
gettext.bindtextdomain('thisapp', './locale/')
gettext.textdomain('thisapp')
_ = gettext.gettext

import twincore, pypacker

# ------------------------------------------------------------------------

pgdebug = 0
verbose = 0
version = "1.0"
keyonly = 0
ncount  = 1
skipcount  = 0
maxx    = 10
lcount  = twincore.INT_MAX

quiet   = 0; writex  = 0
randx   = 0; skipx   = 0
offsx   = 0; delx    = 0
delrx   = 0; delrx2  = 0
backx   = 0; sdelx   = 0
vacx    = 0; recx    = 0
integx  = 0; checkx  = 0

retrx   = ""; getit   = ""
keyx    = ""; datax   = ""
findx   = ""
deffile = "data/pydbase.pydb"
allstr =    " " + \
            string.ascii_lowercase +  string.ascii_uppercase +  \
                string.digits

# ------------------------------------------------------------------------

# Return a random string based upon length

def randstr(lenx):

    strx = ""
    for aa in range(lenx):
        ridx = random.randint(0, len(allstr)-1)
        rr = allstr[ridx]
        strx += str(rr)
    return strx

def help():
    print("Usage: pydebase.py [options] [arg_key arg_data]")
    print(" Options: -h         help (this screen)")
    print("          -V         print version        -|-  -q   quiet on")
    print("          -d         debug level (0-10)   -|-  -v   increment verbosity level")
    print("          -r         write random data    -|-  -w   write fixed record(s)")
    print("          -z         dump backwards(s)    -|-  -i   show deleted record(s)")
    print("          -U         Vacuum DB            -|-  -R   reindex / recover DB")
    print("          -I         DB Integrity check   -|-  -c   set check integrity flag")
    print("          -s         Skip count           -|-  -K   list keys only")
    print("          -y  key    find by key          -|-  -t  key    retrieve by key")
    print("          -o  offs   get data from offset -|-  -e  offs   delete at offset")
    print("          -u  rec    delete at position   -|-  -g  num    get number of recs.")
    print("          -k  key    key to save          -|-  -a  str    data to save ")
    print("          -n  num    number of records to write")
    print("          -p  num    skip number of records on get")
    print("          -l  lim    limit number of records on get")
    print("          -x  max    limit max number of records to get")
    print("          -f  file   input or output file (default: 'data/pydbase.pydb')")
    print("The default action is to dump records to screen in reverse order.")
    print("On the command line, use quotes for multi word arguments.")

# ------------------------------------------------------------------------

def mainfunc():


    ''' Exersize all funtions of the twincore library '''

    global           \
    quiet,   writex,    randx,   skipx , \
    offsx,   delx  ,    delrx,   delrx2, \
    backx,   sdelx ,    vacx ,   recx  , \
    integx,  checkx,   \
    pgdebug, verbose, version,  keyonly, \
    ncount,  skipcount,  maxx,  lcount,    \
    retrx,    getit,   keyx, datax,   \
    findx,   deffile

    opts = []; args = []

    # Old fashioned parsing
    opts_args   = "a:d:e:f:g:k:l:n:o:s:t:u:x:y:p:"
    opts_normal = "chiVrwzvqURIK?"
    try:
        opts, args = getopt.getopt(sys.argv[1:],  opts_normal + opts_args)
    except getopt.GetoptError as err:
        print(_("Invalid option(s) on command line:"), err)
        sys.exit(1)

    for aa in opts:
        if aa[0] == "-d":
            try:
                pgdebug = int(aa[1])
                #print( sys.argv[0], _("Running at debug level"),  pgdebug)
            except:
                pgdebug = 0

        if aa[0] == "-h" or aa[0] == "-?":
            help(); exit(1)
        if aa[0] == "-V":
            print("Version", version);  exit(1)
        if aa[0] == "-v":
            #print("Verbose")
            verbose += 1
        if aa[0] == "-z":
            #print("backx")
            backx = True
        if aa[0] == "-u":
            #print("delrx")
            delrx2 = 1
            delrx = int(aa[1])
        if aa[0] == "-w":
            writex = True
        if aa[0] == "-i":
            sdelx = True
        if aa[0] == "-q":
            #print("Quiet")
            quiet = True
        if aa[0] == "-n":
            ncount = int(aa[1])
            #print("ncount", ncount)
        if aa[0] == "-t":
            retrx = aa[1]
            #print("retrx", retrx)
        if aa[0] == "-l":
            lcount = int(aa[1])
            #print("lcount", lcount)
        if aa[0] == "-x":
            maxx = int(aa[1])
            #print("maxx", maxx)
        if aa[0] == "-s":
            skipcount = int(aa[1])
            #print("skipcount", skipcount)
        if aa[0] == "-f":
            deffile = aa[1]
            #print("deffile", deffile)
        if aa[0] == "-g":
            getit = aa[1]
            #print("getit", getit)
        if aa[0] == "-k":
            keyx = aa[1]
            #print("keyx", keyx)
        if aa[0] == "-a":
            datax = aa[1]
            #print("datax", datax)
        if aa[0] == "-r":
            randx = True
            #print("randx", randx)
        if aa[0] == "-U":
            vacx = True
        if aa[0] == "-K":
            keyonly = True
            #print("vacx", vacx)
        if aa[0] == "-R":
            recx = True
            #print("vacx", vacx)
        if aa[0] == "-p":
            skipx = int(aa[1])
            #print("skipx", skipx)
        if aa[0] == "-y":
            findx = aa[1]
            #print("findx", findx)
        if aa[0] == "-o":
            offsx = aa[1]
            #print("offsx", offsx)
        if aa[0] == "-e":
            delx = aa[1]
            #print("delx", delx)
        if aa[0] == "-c":
            checkx = True
            #print("checkx", checkx)
        if aa[0] == "-I":
            integx = True
            #print("integx", integx)

    #print("args", args)

    # Set some flags
    twincore.core_quiet     = quiet
    twincore.core_pgdebug   = pgdebug
    twincore.core_showdel   = sdelx
    twincore.core_integrity = checkx
    twincore.core_pgdebug   = pgdebug

    # Create our database
    core = twincore.TwinCore(deffile)
    core.core_verbose   = verbose

    # See if we have arguments, save it as data
    if len(args) == 2:
        #print("args", args)
        curr = core.save_data(args[0], args[1])
        sys.exit(0)

    #print(dir(core))

    # Correct maxx
    if maxx == 0 : maxx = 1

    dbsize = core.getdbsize()
    #print("DBsize", dbsize)

    if keyx and datax:
        curr = 0
        if verbose:
            print("adding", keyx, datax)
        for aa in range(ncount):
            curr = core.save_data(keyx, datax)
        #print("curr", curr)
    elif keyx:
        curr = 0
        if verbose:
            print("adding", keyx)
        for aa in range(ncount):
            curr = core.save_data(keyx, "dddd dddd")
        #print("curr", curr)
    elif writex:
        curr = 0;
        if randx:
            for aa in range(ncount):
                curr = core.save_data(randstr(random.randint(2, 10)), randstr(random.randint(10, 20)))
        else:
            for aa in range(ncount):
                curr = core.save_data("111 222", "333 444")
        #print("curr", curr)
    elif findx:
        if lcount == 0: lcount = 1
        ddd = core.find_key(findx, lcount)
        print("ddd", ddd)

    elif keyonly:
        cnt = 0
        if lcount + skipx > dbsize:
            lcount = dbsize - skipx
        for aa in range(skipx, lcount):
            ddd = core.get_rec(aa)
            print(aa, ddd[0])
            cnt += 1

    elif getit:
        getx = int(getit)
        #skipx = dbsize - skipx
        if getx + skipx > dbsize:
            getx = dbsize - skipx
        if skipx < 0:
            skipx = 0
            print("Clipping to dbsize of", dbsize)
        if verbose:
            print("Getting %d records" % getx);
            if skipx:
                print("With skipping %d records" % skipx);

        for aa in range(skipx, getx + skipx):
            ddd = core.get_rec(aa)
            print(aa, ddd)

    elif retrx != "":
        if ncount == 0: ncount = 1
        ddd = core.retrieve(retrx, ncount)
        print(ddd)
    elif offsx:
        ddd = core.get_rec_offs(int(offsx))
        print(ddd)
    elif delx:
        ddd = core.del_rec_offs(int(delx))
        print(ddd)
    elif delrx2:
        ddd = core.del_rec(int(delrx))
        print(ddd)
    elif recx:
        ddd = core.reindex()
        print("reindexed:", ddd, "record(s)")
    elif vacx:
        ddd = core.vacuum()
        print("vacuumed:", ddd, "record(s)")
    elif integx:
        ddd = core.integrity()
        print("integrity check found:", int(ddd), "record(s)")
    else:
        if backx:
            core.dump_data(lcount, skipx)
        else:
            core.revdump_data(lcount, skipx)

if __name__ == "__main__":
    mainfunc()

# EOF
