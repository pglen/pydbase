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

    ooo = []
    dbsize = core.getdbsize()
    for aa in range(dbsize):
        vvv = core.get_rec(aa)
        if vvv:
            ooo.append(vvv)

    core.vacuum()

    dbsize2 = core.getdbsize()

    assert dbsize == dbsize2 + 1

    ddd = []
    for aa in range(dbsize2):
        vvv = core.get_rec(aa)
        if vvv:
            ddd.append(vvv)

    print(ddd); print(ooo)
    assert ooo == ddd

    #assert 0

# EOF
