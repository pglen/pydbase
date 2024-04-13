#!/usr/bin/env python3

import pytest, os, sys, random
from mytest import *
import twincore, pyvpacker

core = None
fname = createname(__file__)
iname = createidxname(__file__)

def setup_module(module):
    """ setup any state specific to the execution of the given module."""
    global core
    core = create_db(fname)
    assert core != 0

    ret = core.save_data("1111", "2222")
    assert ret != 0
    ret = core.save_data("11111", "22222")
    assert ret != 0
    # This is the record that will be found
    ret = core.save_data("111111", "222222")
    assert ret != 0
    ret = core.save_data("111", "222")
    assert ret != 0

def teardown_module(module):
    """ teardown any state that was previously setup with a setup_module
    method.
    """
    uncreate_db()

def setup_function(function):
    #assert 0
    pass

def teardown_function(function):
    #assert tmp_path == ""
    #assert 0, "test here, function %s" % function.__name__
    pass

# ------------------------------------------------------------------------
# Start

def test_get():

    # Get record, verify
    ret = core.get_rec(0)
    assert ret == [b'1111', b'2222']
    assert ret

    ret = core.get_rec(1)
    assert ret
    assert ret == [b'11111', b'22222']

    # Provoke exception
    err = 0
    try:
        ret = core.get_rec(100)
    except:
        err = 1
    assert err == 1

def test_getoffs():

    ret = core.findrecoffs('111', 1)
    #print("ret:", ret)
    assert ret == [134]
    ddd = core.get_rec_byoffs(ret[0])
    assert ddd ==[b'111', b'222']

def test_getoffs2():

    ret2 = core.findrecoffs('11111', 1)
    #print("ret2:", ret2)
    assert ret2 == [98]
    ddd = core.get_rec_byoffs(ret2[0])
    assert ddd ==[b'111111', b'222222']

# EOF
