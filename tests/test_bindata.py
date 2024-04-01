#!/usr/bin/env python3

import pytest, os, sys
from mytest import *
import twincore, pyvpacker

core = None
fname = createname(__file__)
iname = createidxname(__file__)

orgdata = []

# ------------------------------------------------------------------------

def setup_module(module):
    """ setup any state specific to the execution of the given module."""
    global core, orgdata

    try:
        # Fresh start
        os.remove(fname)
        os.remove(iname)
    except:
        #print("on prepare", sys.exc_info())
        pass

    core = twincore.TwinCore(fname)
    assert core != 0

    # Create a database of 500 random binary records
    for aa in range(500):
        key = randbin(random.randint(6, 12))
        val = randbin(random.randint(24, 96))
        ret = core.save_data(key, val)
        assert ret != 0
        orgdata.append([key, val])

def teardown_module(module):
    """ teardown any state that was previously setup with a setup_module
    method.
    """
    try:
        # No dangling data
        os.remove(fname)
        os.remove(iname)
        pass
    except:
        print(sys.exc_info())
        #assert 0
        pass

    #assert 0

def test_bindata(capsys):

    dbsize = core.getdbsize()

    ddd = []
    for aa in range(dbsize):
        vvv = core.get_rec(aa)
        ddd.append(vvv)

    # print(orgdata);  print(ddd)

    assert orgdata == ddd

# EOF
