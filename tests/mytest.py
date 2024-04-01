import os, string, random, sys

sys.path.append("..")
sys.path.append("../pydbase")

import twincore
import pyvpacker

# Return a random string based upon length

allstr =  string.ascii_lowercase +  string.ascii_uppercase

def randstr(lenx):

    strx = ""
    for aa in range(lenx):
        ridx = random.randint(0, len(allstr)-1)
        rr = allstr[ridx]
        strx += str(rr)
    return strx

# ------------------------------------------------------------------------

test_dir = "test_data"

if not os.path.isdir(test_dir):
    os.mkdir(test_dir)

tmpfile = ""

#tmpfile = os.path.splitext(os.path.basename(__file__))[0]
#tmpfile = randstr(8)

# This one will get the last one
for mm in sys.modules:
    if "test_" in mm:
        #print("mod", mm)
        tmpfile = mm

#print("tmpfile", tmpfile)


baseall = os.path.join(test_dir, tmpfile)
print("baseall", baseall)
#assert 0

def createname(file):
    datafile = os.path.splitext(os.path.basename(file))[0]
    return test_dir + os.sep + datafile + ".pydb"

def createidxname(file):
    datafile = os.path.splitext(os.path.basename(file))[0]
    return test_dir + os.sep + datafile + ".pidx"

gl_fname = ""
gl_iname = ""

def create_db(fname = ""):

    global gl_fname, gl_iname

    core = None

    if fname == "":
       gl_fname = createname(__file__)
       gl_iname = createidxname(__file__)
    else:
       gl_fname = createname(fname)
       gl_iname = createidxname(fname)

    #print("used", gl_fname, gl_iname)

    try:
        # Fresh start
        os.remove(gl_fname)
        os.remove(gl_iname)
        pass
    except:
        #print("Cannot delete", sys.exc_info())
        pass

    # We aquire a global lock so multiople pytests are OK
    lockname = os.path.splitext(gl_fname)[0] + ".xlock"
    lock = twincore.FileLock(lockname)
    lock.waitlock()
    print("lock", lock, lock.lockname)

    try:
        core = twincore.TwinCore(gl_fname)
        #print(core)
        #assert 0
    except:
        print(sys.exc_info())

    return core

def uncreate_db(fname = ""):

    #if fname == "":
    #   fname = baseall + ".pydb"
    #   iname = baseall + ".pidx"

    try:
        # Fresh start for next run
        os.remove(gl_fname)
        os.remove(gl_iname)
        pass
    except:
        pass

# ------------------------------------------------------------------------
# Support utilities

# Return a random string based upon length

def randbin(lenx):

    strx = ""
    for aa in range(lenx):
        ridx = random.randint(0, 255)
        strx += chr(ridx)
    return strx.encode("cp437", errors="ignore")


# EOF
