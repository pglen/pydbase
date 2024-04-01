#!/usr/bin/env python3

import pytest, os, sys, random
from mytest import *
import twincore, pyvpacker

# --------------------------------------------------------------
# Test for pydbase integrity test

core = None

fname = createname(__file__)
iname = createidxname(__file__)

orgdata = []

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

    core = create_db(fname)
    assert core != 0

    kkk = 1000000; vvv = 1000
    # Create a database of xxx records
    for aa in range(500):
        ret = core.save_data(str(kkk), str(vvv))
        orgdata.append([str(kkk).encode(), str(vvv).encode()])
        assert ret != 0
        kkk += 1; vvv += 1
    #assert 0

def teardown_module(module):
    """ teardown any state that was previously setup with a setup_module
    method.
    """
    try:
        # Fresh start
        os.remove(fname)
        os.remove(iname)
    except:
        #print(sys.exc_info())
        pass

def test_reindex(capsys):

    dbsize = core.getdbsize()
    #print("dbsize", dbsize)
    #assert 0

    ddd = []
    for aa in range(dbsize):
        vvv = core.get_rec(aa)
        ddd.append(vvv)

    #print(ddd); print(); print(orgdata)
    assert ddd == orgdata

    core.reindex()
    dbsize2 = core.getdbsize()

    assert dbsize == dbsize2

    nnn = []
    try:
        for aa in range(dbsize2):
            vvv = core.get_rec(aa)
            nnn.append(vvv)
    except:
        pass

    assert nnn == ddd

# EOF
