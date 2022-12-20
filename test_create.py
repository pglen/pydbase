
import pytest, twincore, pypacker

core = None

def setup_function(function):
    #assert tmp_path == ""
    #assert core != 0
    pass

def test_create():
    global core
    core = twincore.TwinCore()
    assert core != 0

def test_write():
    print("write", core)
    ret = core.save_data("111", "222")
    assert ret != 0

def test_read():
    print("read", core)
    ret = core.get_rec(2)
    assert ret != 0

def test_create_file(tmp_path):
    #assert tmp_path == ""
    print("tmp_path", tmp_path)
    #assert core == 0
    pass

# EOF
