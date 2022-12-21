
import pytest, twincore, pypacker, os

#pytest_plugins = "pytester"

core = None

def setup_module(module):
    """ setup any state specific to the execution of the given module."""
    global core
    try:
        # Fresh start
        os.remove("data/tests.pydb")
        os.remove("data/tests.pidx")
    except:
        pass

    core = twincore.TwinCore("data/tests.pydb")
    assert core != 0

def teardown_module(module):
    """ teardown any state that was previously setup with a setup_module
    method.
    """
    pass

def setup_function(function):
    #assert 0
    pass

def teardown_function(function):
    #assert tmp_path == ""
    #assert 0, "test here, function %s" % function.__name__
    pass

# ------------------------------------------------------------------------
# Start

def test_create(tmp_path):
    global core
    try:
        # Fresh start
        os.remove("data/tests.pydb")
        os.remove("data/tests.pidx")
    except:
        pass

    #print(pytest.Pytester.path)
    #assert 0
    #print(tmp_path)
    #assert 0
    #core = twincore.TwinCore("data/tests.pydb")
    #assert core != 0

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
