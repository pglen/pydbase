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
        opts, args = getopt.getopt(sys.argv[1:], "d:h?f:vxctVown:ql:s:")
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

        if aa[0] == "-s":
            scount = int(aa[1])
            #print("scount", scount)

        if aa[0] == "-f":
            deffile = aa[1]
            #print("deffile", deffile)

    #print("args", args)

    core = twincore.DbTwinCore(deffile)

    twincore.core_quiet = quiet
    twincore.core_verbose = verbose

    #sys.exit(0)

    # Test one
    #core.save_data("111 " + randstr(12) + " 222", "333 " + randstr(24) + " 444")
    #core.save_data("111 222", "333 444")
    #sys.exit(0)

    if writex:
        for aa in range(ncount):
            core.save_data(randstr(4), randstr(8))
            #core.save_data("111 222", "333 444")
    else:
        core.dump_data(lcount, scount)

# EOF


