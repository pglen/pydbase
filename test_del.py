# Test for pydbase

import os, pytest
import twincore, pypacker

core = None

def setup_module(module):
    """ setup any state specific to the execution of the given module."""
    global core
    try:
        # Fresh start
        os.remove("test_data/tests_delete.pydb")
        os.remove("test_data/tests_delete.pidx")
    except:
        #print(sys.exc_info())
        pass

    core = twincore.TwinCore("test_data/tests_delete.pydb")
    assert core != 0

    ret = core.save_data("1111", "2222")
    assert ret != 0
    ret = core.save_data("11111", "22222")
    assert ret != 0
    ret = core.save_data("111", "222")
    assert ret != 0

def test_del(capsys):

    core.del_recs(b"11111")
    core.del_recs("111")

    core.dump_data(twincore.INT_MAX)
    captured = capsys.readouterr()

    out =   "0     pos    32 Data: b'1111' Data2: b'2222'\n"

    assert captured.out == out

# EOF
