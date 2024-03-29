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
    try:
        # Fresh start
        os.remove(fname)
        os.remove(iname)
    except:
        #print(sys.exc_info())
        pass

    core = twincore.TwinCore(fname)
    assert core != 0

    ret = core.save_data("1111", "2222")
    assert ret != 0
    ret = core.save_data("11111", "22222")
    assert ret != 0
    ret = core.save_data("111", "222")
    assert ret != 0

    ret = core.del_rec_bykey("111")

    twincore.base_showdel = True
    core.dump_data()

    #ret = core.save_data("1", "2")
    #assert ret != 0
    #ret = core.save_data("11", "22")
    #assert ret != 0
    #ret = core.save_data("111", "222")
    #assert ret != 0

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

def test_vacuum(capsys):

    core.pgdebug = 0
    core.vacuum()

    core.dump_data()

    #assert 0

    captured = capsys.readouterr()

    out =   "0     pos    32 Data: b'1111' Data2: b'2222'\n"    \
            "1     pos    64 Data: b'11111' Data2: b'22222'\n"

            #"2     pos    98 Data: b'111' Data2: b'222'\n"

    assert captured.out == out

    #assert 0

# EOF
