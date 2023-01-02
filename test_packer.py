# Test for pydbase

import os, pytest
import twincore, pypacker

packer = None

def setup_module(module):
    """ setup any state specific to the execution of the given module."""

    global packer
    packer = pypacker.packbin()

    try:
        # Fresh start
        pass
    except:
        #print(sys.exc_info())
        pass

def test_packer(capsys):

    ddd = packer.encode_data("", "1234")
    print(ddd)
    captured = capsys.readouterr()

    out = "pg s1 's' s4 '1234' \n"
    assert captured.out == out

def test_packer_complex(capsys):

    org = [11, ["ss", "dd"], "rr"]
    ddd = packer.encode_data("", org)
    #print(ddd)
    #captured = capsys.readouterr()
    eee = packer.decode_data(ddd)
    assert org == eee[0]


# EOF
