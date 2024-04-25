#!/usr/bin/env python3

import pytest, os, sys

fff = __file__[:]
from mytest import *

core = None
fname = createname(__file__)
iname = createidxname(__file__)

def setup_module(module):
    """ setup any state specific to the execution of the given module."""
    global core
    core = create_db(fname)
    assert core != None

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

def pre(ccc, head):
    print("precaLL", ccc, head)

def post(ccc, headx):

    global gl_ccc
    print("postcaLL", ccc, headx)
    gl_ccc = core
    assert ccc == core

# ------------------------------------------------------------------------
# Start

def test_call(capsys):

    print("write", core)
    ret = core.save_data("1111", "2222")
    print(ret)
    #assert ret != 0
    ret = core.save_data("11111", "22222")
    #assert ret != 0

    core.preexec = pre
    core.postexec = post
    ret = core.save_data("111", "222")
    #assert ret != 0
    assert gl_ccc == core

    #assert 0

    #for aa in range(core.getdbsize()):
    #    print( core.get_rec(aa))

def test_get(capsys):

    ret = core.get_rec(2)
    assert ret != 0
    assert ret == [b'111', b'222']

def test_read(capsys):

    #for aa in range(core.getdbsize()):
    #    print( core.get_rec(aa))

    ret = core.retrieve("111")
    print(ret)
    assert ret == [[b'111', b'222']]

    ret = core.retrieve("1111")
    assert ret == [[b'1111', b'2222']]


# EOF

