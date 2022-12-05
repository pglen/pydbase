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

#import dbcore
import memcore

pgdebug = 0
verbose = 0
version = "1.0"

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
    print("Helping")

if __name__ == "__main__":

    opts = []; args = []

    try:
        opts, args = getopt.getopt(sys.argv[1:], "d:h?fvxctVow")
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

    #print("args", args)

    fname = "first.pydb"
    core = memcore.DbCore(fname)
    #core.save_data("111 " + randstr(12) + " 222", "333 " + randstr(24) + " 444")

    if writex:
        core.save_data("111 222", "333  444")
    else:
        core.dump_data()

# EOF


