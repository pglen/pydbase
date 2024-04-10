#!/usr/bin/env python3

import pytest, os, sys
from mytest import *

import twinchain, pyvpacker

core = None
fname = createname(__file__)
iname = createidxname(__file__)

pay  = "payload string " * 2

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

    core = twinchain.TwinChain(fname)
    assert core != 0

    for aa in range(2):
        core.append(pay)
    core.flush()

def teardown_module(module):
    """ teardown any state that was previously setup with a setup_module
    method.
    """

    try:
        # No dangling data
        #os.remove(fname)
        #os.remove(iname)
        pass
    except:
        print(sys.exc_info())
        #assert 0
        pass

    #assert 0

def test_data(capsys):

    dbsize = core.getdbsize()
    payload = core.get_payload(dbsize-1)
    #print(payload[1].decode(), pay)
    print(payload[1])
    assert payload[1] == pay

    for aa in range(1, dbsize-1):
        ppp = core.linkintegrity(aa)
        assert ppp == True

    for aa in range(1, dbsize-1):
        ppp = core.checkdata(aa)
        assert ppp == True

def test_links(capsys):

    print(fname)
    fp = open(fname, "rb")
    buff = fp.read(); fp.close()

    # Damage file buffer rec 1 -- make sure it is in relevant section
    # Please note that this is a hack to test damage
    pos = 0x440
    buff = buff[:pos] + b'x' + buff[pos+1:]

    fp2 = open(fname, "wb")
    fp2.write(buff);  fp2.close()

    # Changed file buffer, reload
    core2 = twinchain.TwinChain(fname)
    assert core2 != 0
    dbsize = core2.getdbsize()

    # All others
    #for aa in range(1, dbsize):
    #    print(aa, core2.get_payload(aa))

    # The succeeding record
    ppp = core2.linkintegrity(0)
    assert ppp == True

    # The failing record
    ppp = core2.linkintegrity(1)
    assert ppp == False

    # Test print of the setup
    #for aa in range(0, dbsize):
    #    ppp = core2.checkdata(aa)
    #    print("data", aa, ppp)
    #
    #for aa in range(0, dbsize):
    #    ppp = core2.linkintegrity(aa)
    #    print("link", aa, ppp)
    #assert 0

# EOF
