#!/usr/bin/env python3

import  os, sys, getopt, signal, select, socket, time, struct
import  random, stat, os.path, datetime, threading, warnings
import  string

import gettext
gettext.bindtextdomain('thisapp', './locale/')
gettext.textdomain('thisapp')
_ = gettext.gettext

import twincore, pypacker

packer = pypacker.packbin()
core = twincore.TwinCore("second.pydb")

# This is a hybrid of many types
org = 1, 2,  "aa", ["bb", b"dd",]

print("org:", org)
packed = packer.encode_data("", *org)
print("packed:", packed)
unpacked = packer.decode_data(packed)
print("unpacked:", unpacked)

thiskey = "ThisKey"     # use this key for save / retrieve

# Send / Retrieve data from DB

core.save_data(thiskey, packed)
rec_arr = core.retrieve(thiskey, 1)[0]

# The data went through encoding to binary, decode
data = rec_arr[1].decode("cp437")
print ("rec_arr:", data)
rec_arr_upacked = packer.decode_data(data)
print ("rec_arr_upacked:", rec_arr_upacked)

# EOF

