#!/usr/bin/env python3

import pytest, os, sys
from mytest import *

# Test for pydbase locking

ttt = "test_ro"
fff = "test_ro/test_file.pydb"
xxx = "test_ro/test_file.pidx"
lll = "test_ro/test_file.lock"

core = None

def setup_module(module):
    """ setup any state specific to the execution of the given module."""
    pass

def teardown_module(module):
    """ teardown any state that was previously setup with a setup_module """
    pass


def setup_function(function):
    #assert 0
    pass

def chmod_noraise(fname, acc):
    try:
        os.chmod(fname, acc)
    except:
        pass

def del_noraise(fname):
    try:
        os.remove(fname)
    except:
        pass

def teardown_function(function):

    # Allow access again
    chmod_noraise(ttt, 0o777)
    chmod_noraise(fff, 0o777)
    chmod_noraise(xxx, 0o777)
    chmod_noraise(lll, 0o777)

    del_noraise(fff)
    del_noraise(xxx)
    del_noraise(lll)
    del_noraise(ttt)

# ------------------------------------------------------------------------
# Start

def test_ro():

    global core

    if not os.path.isdir(ttt):
        os.mkdir(ttt)
    try:
        fp = open(fff, "w+")
        fp.close()
        os.chmod(fff, 0o444)
        os.chmod(ttt, 0o444)
    except:
        print(sys.exc_info())

    #print(os.stat(fff))
    exc = False
    try:
        core = twincore.TwinCore(fff)
    except:
        exc = 1
    assert exc == True

    # Testing for lock
    if os.path.isfile(lll):
        print("Unexpected lock file")
        assert 0
    core = 0

# EOF


