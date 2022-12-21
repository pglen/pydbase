#!/usr/bin/env python3

import  os, sys, getopt, signal, select, socket, time, struct
import  random, stat, os.path, datetime, threading, warnings
import string

#import gi
#gi.require_version("Gtk", "3.0")
#from gi.repository import Gtk
#from gi.repository import Gdk
#from gi.repository import GObject
#from gi.repository import GLib

import gettext
gettext.bindtextdomain('thisapp', './locale/')
gettext.textdomain('thisapp')
_ = gettext.gettext

import twincore, pypacker

# ------------------------------------------------------------------------

pgdebug = 0
verbose = 0
version = "1.0"
ncount  = 1
scount  = 0
maxx    = 10
lcount  = twincore.INT_MAX

quiet   = 0; writex  = 0
randx   = 0; skipx   = 0
offsx   = 0; delx    = 0
delrx   = 0; delrx2  = 0
backx   = 0; sdelx   = 0
vacx    = 0; recx    = 0

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
    print("Usage: pydebase.py [options]")
    print("  Options: -h         help (this screen)")
    print("           -V         print version        ||  -q   quiet on")
    print("           -d         debug level (0-10)   ||  -v   increment verbosity level")
    print("           -r         write random data    ||  -w   write record(s)")
    print("           -z         dump backwards(s)    ||  -i   show deleted record(s)")
    print("           -U         Vacuum DB            ||  -R   reindex / recover DB")
    print("           -f  file   input or output file (default: 'pydbase.pydb')")
    print("           -n  num    number of records to write")
    print("           -g  num    get number of records")
    print("           -p  num    skip number of records on get")
    print("           -l  lim    limit number of records on get")
    print("           -x  max    limit max number of records to get")
    print("           -k  key    key to save (quotes for multi words)")
    print("           -a  str    data to save (quotes for multi words)")
    print("           -y  key    find by key")
    print("           -t  key    retrieve by key")
    print("           -o  offs   get data from offset")
    print("           -e  offs   delete at offset")
    print("           -u  rec    delete at position")
    print("The default action is to dump records to screen in reverse order.")

# ------------------------------------------------------------------------

if __name__ == "__main__":

    ''' Exersize all funtions of the twincore library '''

    opts = []; args = []

    # Old fashioned parsing
    try:
        opts_args   = "a:d:e:f:g:k:l:n:o:s:t:u:x:y:"
        opts_normal = "chiVrwzvqUR?"
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
            scount = int(aa[1])
            #print("scount", scount)
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
            #print("vacx", vacx)
        if aa[0] == "-R":
            recx = True
            #print("vacx", vacx)
        if aa[0] == "-p":
            skipx = aa[1]
            #print("skipx", skipx)
        if aa[0] == "-y":
            findx = aa[1]
            #print("skipx", skipx)
        if aa[0] == "-o":
            offsx = aa[1]
            #print("skipx", skipx)
        if aa[0] == "-e":
            delx = aa[1]
            #print("skipx", skipx)

    #print("args", args)

    # Set some flags
    twincore.core_quiet = quiet
    twincore.core_verbose = verbose
    twincore.core_pgdebug = pgdebug
    twincore.core_showdel = sdelx
    twincore.core_pgdebug = pgdebug

    # Create our database
    core = twincore.TwinCore(deffile)

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

    elif getit:
        if maxx > dbsize:
            maxx = dbsize
        if verbose:
            print("Getting %d records" % maxx);
        ddd = core.get_rec(int(getit))
        print(ddd)

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
    else:
        if backx:
            core.dump_data(lcount, skipx)
        else:
            core.revdump_data(lcount, skipx)

# EOF
