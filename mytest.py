
import os, string, random

import twincore

test_dir = "test_data"
tmpfile = os.path.splitext(os.path.basename(__file__))[0]
baseall = os.path.join(test_dir, tmpfile)

#print(baseall)

def create_db():
    try:
        # Fresh start
        os.remove(baseall + ".pydb")
        os.remove(baseall + ".pidx")
    except:
        pass

    try:
        core = twincore.TwinCore(baseall + ".pydb")
    except:
        print(sys.exc_info())
    return core

def uncreate_db():
    try:
        # Fresh start
        os.remove(baseall + ".pydb")
        os.remove(baseall + ".pidx")
    except:
        pass


# ------------------------------------------------------------------------
# Support utilities

allstr =    " " + \
            string.ascii_lowercase +  string.ascii_uppercase +  \
                string.digits

# Return a random string based upon length

def randbin(lenx):

    strx = ""
    for aa in range(lenx):
        ridx = random.randint(0, 255)
        strx += chr(ridx)
    return strx.encode("cp437", errors="ignore")

# Return a random string based upon length

def randstr(lenx):

    strx = ""
    for aa in range(lenx):
        ridx = random.randint(0, len(allstr)-1)
        rr = allstr[ridx]
        strx += str(rr)
    return strx

# EOF
