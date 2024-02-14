#!/usr/bin/env python3

import pytest, os, sys
from mytest import *


import twincore, pypacker

core = None
fname = createname(__file__)
iname = createidxname(__file__)

ddd = \
 ['rput', 'vote',
 ['1707765075.806346', '39c91dc0c9d811ee99d0eb7f258547e4',
 {'PayLoad': {'Default': '', 'Vote': 0,
  'UID': 'ca81f62ed5574acaa4a105192da5c631'}},
  #{'_PowRand': b'\x84\xcd\xb2\xb3\xb9\xe9t\xcd\x15\xe2\x95\xb4'},
  {'_Hash': 'd0b28280f5810041336982b423522d67e740692c36f7a311fdcc9fd3ef419d0f'},
  {'_Proof': 'dfd58c2cc281cee281631d20a2032332af26d0df8a8f758043f2098ff9bae000'}
  ]]

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

    core = twincore.TwinCore(fname)
    assert core != 0

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


def test_data(capsys):

    print(ddd[2][0], ddd[2][1:])
    dbsize = core.getdbsize()
    core.save_data(ddd[2][0], 'zzz', w   ddd[2][1:])


    try:
        # No dangling data
        #os.remove(fname)
        #os.remove(iname)
        pass
    except:
        print(sys.exc_info())
        #assert 0
        pass

# EOF
