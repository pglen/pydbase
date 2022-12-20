
import pytest, twincore, pypacker, os

core = None

def setup_function(function):
    #assert tmp_path == ""
    #assert core != 0
    pass

def test_create():
    global core
    os.remove("data/tests.pydb")
    os.remove("data/tests.pidx")

    core = twincore.TwinCore("data/tests.pydb")
    assert core != 0

def test_write():
    print("write", core)
    ret = core.save_data("1111", "2222")
    assert ret != 0
    ret = core.save_data("11111", "22222")
    assert ret != 0
    ret = core.save_data("111", "222")
    assert ret != 0

def test_get():
    print("get", core)
    ret = core.get_rec(2)
    assert ret != 0

def test_read():
    print("read", core)
    ret = core.retrieve("111")
    assert ret == [[b'111', b'222']]

def test_create_file(tmp_path):
    #assert tmp_path == ""
    print("tmp_path", tmp_path)
    #assert core == 0
    pass

# EOF
