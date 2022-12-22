
import os, pytest
import twincore, pypacker

core = None

def setup_module(module):
    """ setup any state specific to the execution of the given module."""
    global core
    try:
        # Fresh start
        os.remove("data/tests_vacuum.pydb")
        os.remove("data/tests_vacuum.pidx")
    except:
        #print(sys.exc_info())
        pass

    core = twincore.TwinCore("data/tests_vacuum.pydb")
    assert core != 0

    ret = core.save_data("1111", "2222")
    assert ret != 0
    ret = core.save_data("11111", "22222")
    assert ret != 0
    ret = core.save_data("111", "222")
    assert ret != 0

    #ret = core.save_data("1", "2")
    #assert ret != 0
    #ret = core.save_data("11", "22")
    #assert ret != 0
    #ret = core.save_data("111", "222")
    #assert ret != 0

def test_vacuum(capsys):

    core.vacuum()
    core.dump_data(twincore.INT_MAX)
    captured = capsys.readouterr()

    out =   "0     pos    32 Data: b'1111' Data2: b'2222'\n"    \
            "1     pos    64 Data: b'11111' Data2: b'22222'\n"  \
            "2     pos    98 Data: b'111' Data2: b'222'\n"

    assert captured.out == out

# EOF
