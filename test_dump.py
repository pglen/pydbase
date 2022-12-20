
import pytest, twincore, pypacker

def test_one():
    print("one")

def test_save():

    core = twincore.TwinCore()
    assert core

    for aa in range(10):
        core.save_data("aaa aaa", "dddd dddd")

    core.dump_data(0xffff)


# EOF
