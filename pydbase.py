#!/usr/bin/env python3

import  os, sys, getopt, signal, select, socket, time, struct
import  random, stat, os.path, datetime, threading, warnings
import string

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GObject
from gi.repository import GLib

import gettext
gettext.bindtextdomain('thisapp', './locale/')
gettext.textdomain('thisapp')
_ = gettext.gettext

import twincore

pgdebug = 0
verbose = 0
version = "1.0"
ncount  = 1
scount  = 0
lcount  = 0xffffffff
quiet   = 0
maxx    = 10
writex  = 0
randx   = 0
skipx   = 0
offsx   = 0
delx    = 0

getit   = ""
keyx    = ""
datax   = ""
findx   = ""

deffile = "data/pydbase.pydb"

allstr =    " " + \
            string.ascii_lowercase +  string.ascii_uppercase +  \
                string.digits

def randstr(lenx):

    strx = ""
    for aa in range(lenx):
        ridx = random.randint(0, len(allstr)-1)
        rr = allstr[ridx]
        strx += str(rr)

    return strx



def help():
    print()
    print("Usage: pydebase.py [options]")
    print()
    print("  Options: -h            help (this screen)")
    print("           -V            print version")
    print("           -d            debug level (unused)")
    print("           -v            verbosity on")
    print("           -q            quiet on")
    print("           -r            write random data")
    print("           -w            write record(s)")
    print("           -f  file      input or output file (default: 'first.pydb')")
    print("           -n  num       number of records to write")
    print("           -g  num       get number of records")
    print("           -p  num       skip number of records on get")
    print("           -l  lim       limit number of records on get")
    print("           -x  max       limit max number of records to get")
    print("           -k  key       key to save (quotes for multi words)")
    print("           -a  str       data to save (quotes for multi words)")
    print("           -y  key       find by key")
    print("           -o  offs      get data from offset")
    print("           -e  offs      delete at offset")
    print("The default action is to dump records to screen in reverse order.")

# ------------------------------------------------------------------------

if __name__ == "__main__":

    opts = []; args = []

    try:
        opts, args = getopt.getopt(sys.argv[1:], "d:h?f:vx:ctVo:rwn:ql:s:g:k:a:y:e:")
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
            verbose = True

        if aa[0] == "-w":
            writex = True

        if aa[0] == "-q":
            quiet = True
            #print("Quiet")

        if aa[0] == "-n":
            ncount = int(aa[1])
            #print("ncount", ncount)

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

    core = twincore.DbTwinCore(deffile)

    twincore.core_quiet = quiet
    twincore.core_verbose = verbose
    twincore.core_pgdebug = pgdebug

    # Correct maxx
    if maxx == 0 : maxx = 1

    dbsize = core.getdbsize()
    #print("DBsize", dbsize)

    # Test one
    #core.save_data("111 " + randstr(12) + " 222", "333 " + randstr(24) + " 444")
    #core.save_data("111 222", "333 444")
    #sys.exit(0)

    if keyx and datax:
        if verbose:
            print("adding", keyx, datax)
        for aa in range(ncount):
            core.save_data(keyx, datax)

    elif writex:
        if randx:
            for aa in range(ncount):
                core.save_data(randstr(4), randstr(8))
        else:
            for aa in range(ncount):
                core.save_data("111 222", "333 444")

        #print("Must specify data")
        #sys.exit(0)

    elif findx:
        if lcount == 0: lcount = 1
        ddd = core.find_key(findx, lcount)
        print("ddd", ddd)

    elif getit:
        if maxx > dbsize:
            maxx = dbsize
        if verbose:
            print("Getting %d records" % maxx);
        #for aa in range(maxx):
        ddd = core.get_rec(int(getit))
        print(ddd)

    elif offsx:
        ddd = core.get_rec_offs(int(offsx))
        print(ddd)

    elif delx:
        ddd = core.del_rec_offs(int(delx))
        print(ddd)

    else:
        #core.dump_data(lcount, scount)
        core.revdump_data(lcount) #, scount)

# EOF
