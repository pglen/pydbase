#!/usr/bin/env python3

'''
'''

import  os, sys, getopt, signal, select, socket, time, struct
import  random, stat, os.path, datetime, threading, subprocess
import  struct, io, traceback, hashlib, traceback, argparse

try:
    import fcntl
except:
    fcntl = None

base = os.path.dirname(os.path.realpath(__file__))

#print("testdrive")

def diff(expectx, actualx):

    ''' Compare values, display string in Color '''

    if expectx == actualx:
        return "\033[32;1mOK\033[0m"
    else:
        return"\033[31;1mERR\033[0m"

def obtain(cmd):
    exec = cmd.split()
    if args.debug > 1:
        print("exec:", exec)
    ret = subprocess.Popen(exec, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    comm = ret.communicate()
    return comm[0]

# Fresh start, no data
try:
    os.remove("pydbase.pydb")
    os.remove("pydbase.pidx")
except:
    pass

def send_expect(context, sendx, expectx):

    ''' evaluate Send -- EXPECT sequence '''

    ret = obtain(sendx)
    if args.debug > 2:
        print("got: ", ret)

    err = diff(ret, expectx)

    # If no context, we do not want any printing
    if context:
        print(context, "\t", err)

    if args.verbose:
        # On error tell us the expected result
        if ret != expectx:
            print(ret)

# String triplet per test.  Context string and a pair send / expect strings

work = [ \
    ["", "./dbaseadm.py -k test -a testdata", b""],

    [ "Dump data", "./dbaseadm.py -m",
           b"0     pos    32 Data: b'test' Data2: b'testdata'\n"],

    [ "Create data2", "./dbaseadm.py -k test2 -a testdata2", b""],

    ["Dump data", "./dbaseadm.py -m",
         b"0     pos    68 Data: b'test2' Data2: b'testdata2'\n"\
         b"1     pos    32 Data: b'test' Data2: b'testdata'\n"],

    [ "", "./dbaseadm.py -k test3 -a testdata3", b""],
    [ "", "./dbaseadm.py -k test4 -a testdata4", b""],
    [ "", "./dbaseadm.py -k test5 -a testdata5", b""],

    ["Get data", "./dbaseadm.py -t test",
         b"[[b'test', b'testdata']]\n", ],

    ["Find data", "./dbaseadm.py -F test",
        b"[[b'test5', b'testdata5'], [b'test4', b'testdata4'], "\
        b"[b'test3', b'testdata3'], [b'test2', b'testdata2'], "\
        b"[b'test', b'testdata']]\n", ],
    ]

def mainloop():

    if args.readx:
        try:
            with open(args.readx) as fp:
                testx = fp.read()
        except:
            print("Cannot open file", "'" + args.readx + "'")
            sys.exit()
        test_case = eval(testx)
        for aa in test_case:
            send_expect(aa[0], aa[1], aa[2])
    else:
        for aa in work:
            send_expect(aa[0], aa[1], aa[2])


parser = argparse.ArgumentParser(description='Test send/expect by executing sub commands')

parser.add_argument("-v", '--verbose', dest='verbose',
                    default=0,  action='count',
                    help='verbocity on (default: off)')

parser.add_argument("-r", '--read', dest='readx',
                    default=0,  action='store',
                    help='Read test from file)')

parser.add_argument("-d", '--debug', dest='debug',
                    default=0,  type=int, action='store',
                    help='Debug level')

version = "1.0.0"

def mainfunct():

    global args
    args = parser.parse_args()
    #print(args)
    mainloop()

if __name__ == "__main__":
    mainfunct()

# EOF
