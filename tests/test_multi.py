#!/usr/bin/env python3

import pytest, os, sys, threading
from mytest import *
import twincore, pyvpacker

core = None
fname = createname(__file__)
iname = createidxname(__file__)

# ------------------------------------------------------------------------

def setup_module(module):
    """ setup any state specific to the execution of the given module."""
    global core

    try:
        # Fresh start
        os.remove(fname)
        os.remove(iname)
    except:
        #print(sys.exc_info())
        pass

    core = twincore.TwinCore(fname)
    assert core != 0


def teardown_module(module):

    try:
        # No dangling data
        os.remove(fname)
        os.remove(iname)
        pass
    except:
        #print(sys.exc_info())
        pass

# Thread to fill the DB

def threadproc():

    #print("started thread")

    # Create a database of random records
    for aa in range(10):
        #key = randbin(random.randint(6, 12))
        #val = randbin(random.randint(24, 96))
        key = randstr(random.randint(6, 12))
        val = randstr(random.randint(24, 96))
        ret = core.save_data(str(key), str(val))
        assert ret != 0


def test_adders(capsys):

    # Start a handful of threads
    ttt = []
    for aa in range(200):
        tt = threading.Thread(target=threadproc)
        ttt.append(tt)
        tt.run()

    # Wait for all to finish
    while 1:
        aa = False
        for tt in ttt:
            if tt.is_alive():
                aa = True
        if not aa:
            # If none alive
            break
        sleep(.1)

# If the DB is the right size, and not damaged

def test_integrity(capsys):

    ddd = core.integrity_check()
    assert len(ddd) == 2

    assert ddd[0] == 2000
    assert ddd[0] == ddd[1]

    #print (ddd)
    #assert 0


# EOF
