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
    ret = core.get_rec(2)
    assert ret == [b'111', b'222']

def test_getoffs():

    # This is in place
    ret = core.save_data("11111", "333", True)
    #print(ret)
    assert ret == 64

    ret4 = core.get_rec_byoffs(ret)
    #print(ret4)
    assert ret4 == [b'11111', b'333  ']

def test_finder():

    ret2 = core.findrec("11111", 1)
    #print(ret2)
    assert ret2 == [[b'11111', b'333  ']]

    ret3 = core.get_rec(1)
    #print(ret3)
    assert ret3 == [b'11111', b'333  ']

def test_bigger():

    org = core.findrecpos("11111", 1)
    #print("org", org)

    # This is in place, but longer
    ret = core.save_data("11111", "444444", True)
    #print("save bigger data", ret)
    assert ret != org

    ret4 = core.get_rec_byoffs(ret)
    #print("get _rec_byoffs", ret4)
    assert ret4 == [b'11111', b'444444']

    ret5 = core.save_data("11111", "555555", True)
    assert ret == ret5

    ret6 = core.get_rec_byoffs(ret5)
    assert ret6 == [b'11111', b'555555']

    #core.dump_data()
    #assert 0

# EOF
