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
getit = ""
keyx  = ""
datax = ""
maxx  = 10

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


writex = 0

def help():
    print("Usage: pydebase.py [opt]")
    print("Options: ")
    print("         -h   help")
    print("         -w   write record")
    print("         -n   number of records")
    print("         -V   print version")


if __name__ == "__main__":

    opts = []; args = []

    try:
        opts, args = getopt.getopt(sys.argv[1:], "d:h?f:vx:ctVown:ql:s:g:k:a:")
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

    #print("args", args)

    core = twincore.DbTwinCore(deffile)

    twincore.core_quiet = quiet
    twincore.core_verbose = verbose

    # Correct maxx
    if maxx == 0 : maxx = 1

    # Test one
    #core.save_data("111 " + randstr(12) + " 222", "333 " + randstr(24) + " 444")
    #core.save_data("111 222", "333 444")
    #sys.exit(0)

    if writex:
        for aa in range(ncount):
            #core.save_data(randstr(4), randstr(8))
            core.save_data("111 222", "333 444")
    elif keyx:
        if not datax:
            print("Must specify data")
            sys.exit(0)
        #print("adding", keyx, datax)
        core.save_data(keyx, datax)

    elif getit:
        start = 0
        for aa in range(maxx):
            ddd = core.get_data(getit, start)
            if not ddd:
                break

            start = ddd[0] + 1     # Start fro here

            print("ddd", ddd)
    else:
        core.dump_data(lcount, scount)

# EOF


