
import pytest, twincore, pypacker

core = None

def setup_function(function):
    global core
    print("setting up", function)
    core = twincore.TwinCore()
    assert core != 0

def test_one():
    print("one")
    assert 1

def test_write():
    print("write", core)
    core.save_data("111", "222")

def test_create_file(tmp_path):
    #assert tmp_path == ""
    print("tmp_path", tmp_path)
    #assert core == 0
    pass

#print(dir(pytest))
#print(tmp_path)


# EOF
