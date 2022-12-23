
import os, pytest, string, random
import twincore, pypacker

core = None

allstr =    " " + \
            string.ascii_lowercase +  string.ascii_uppercase +  \
                string.digits

# ------------------------------------------------------------------------

# Return a random string based upon length

def randbin(lenx):

    strx = ""
    for aa in range(lenx):
        ridx = random.randint(0, 255)
        strx += chr(ridx)
    return strx.encode("cp437", errors="ignore")


def setup_module(module):
    """ setup any state specific to the execution of the given module."""
    global core
    try:
        # Fresh start
        os.remove("data/test_bytedata.pydb")
        os.remove("data/test_bytedata.pidx")
    except:
        #print(sys.exc_info())
        pass

    core = twincore.TwinCore("data/test_bytedata.pydb")
    assert core != 0

    # Create a database of 5000 random records
    for aa in range(5000):
        key = randbin(random.randint(6, 12))
        val = randbin(random.randint(24, 96))
        ret = core.save_data(str(key), str(val))
        assert ret != 0

def test_bytedata(capsys):

    #core.reindex()
    #core.dump_data(twincore.INT_MAX)
    dbsize = core.getdbsize()
    #print("dbsize", dbsize)
    #assert 0

    ddd = []
    for aa in range(dbsize):
        vvv = core.get_rec(aa)
        ddd.append(vvv)

    #core.core_verbose = 2
    core.reindex()
    dbsize2 = core.getdbsize()
    #core.core_verbose = 0

    nnn = []
    try:
        for aa in range(dbsize2):
            vvv = core.get_rec(aa)
            nnn.append(vvv)
    except:
        pass

    try:
        # No dangling data
        os.remove("data/test_bytedata.pydb")
        os.remove("data/test_bytedata.pidx")
        pass
    except:
        #print(sys.exc_info())
        pass

    assert dbsize == dbsize2
    assert nnn == ddd

# EOF
