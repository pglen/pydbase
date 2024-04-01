#!/usr/bin/env python3

import pytest, os, sys, uuid
from mytest import *

#import twincore, pyvpacker

# Test for pydbase

core = None
fname = createname(__file__)
iname = createidxname(__file__)

bigdata = "Fill Data " * 100
bigbigdata = "Fill Data " * 1000000

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

    ret = core.save_data("1111", "2222")
    assert ret != 0
    ret = core.save_data("11111", "22222")
    assert ret != 0
    ret = core.save_data("111", "222")
    assert ret != 0

    head = str(uuid.uuid1())
    ret = core.save_data(head, bigdata)
    assert ret != 0

    ret = core.save_data(head, bigbigdata)
    assert ret != 0

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

def test_bigdata(capsys):

    dbsize = core.getdbsize()
    #print("dbsize", dbsize)

    assert dbsize == 5

    vvv = core.get_rec(dbsize - 2)
    assert vvv[1].decode() == bigdata

    vvv = core.get_rec(dbsize - 1)
    assert vvv[1].decode() == bigbigdata

    #print(fname)
    #assert 0

# EOF
