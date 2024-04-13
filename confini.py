#!/usr/bin/env python3

import  os, sys, getopt, signal, select, socket, time, struct
import  random, stat, os.path, datetime, threading, warnings
import  string


class SimIni():

    def __init__(self):
        self.datax = {}
        self.errs = []
        self.comments = []

    def save(self, fname):
        sss = ""
        for cc in self.comments:
            sss += cc + "\n"
        sss += "\n"

        for aa in self.datax.keys():
            sss += "[" + str(aa) + "]:\n"
            # Collect this one:
            for bb in self.datax[aa]:
                sss += "  " + str(bb[0]) + " = " + str(bb[1]) + "\n"

        print(sss)

        with open(fname, "w") as fp:
            fp.write(sss)

    def load(self, fname):

        self.errs = []

        try:
            section = ""
            with open(fname, "r") as fp:
                while True:
                    cont = fp.readline()
                    if not cont:
                        break
                    cont = cont.strip()
                    #print("cont", cont)
                    if cont[0] == '':
                        print("Blank line")
                        continue

                    if cont[0] == '#':
                        self.comments.append(cont)
                        continue

                    if cont[0] == '[':
                        cont3 = cont.split("[")
                        cont3 = cont3[1].split("]")
                        section = cont3[0]
                        #print("Section", section)
                        continue
                    cont2 = cont.split()
                    #print("cont2", cont2)
                    try:
                        self.add(section, cont2[0], cont2[2])
                    except:
                        #print(sys.exc_info())
                        self.errs.append((section, cont))

        except:
            print(sys.exc_info())
            pass

    def add(self, section, key, val):
        if not self.datax.get(section):
            self.datax[section] = []
        self.datax[section].append((key, val))

if __name__ == "__main__":

    confx = SimIni()

    confx.load("test.ini")

    print("load:")
    for aa in confx.datax.keys():
        print("[" + aa + "]:")
        for bb in confx.datax[aa]:
            print("   " + bb[0], "=", bb[1])

    print("errs on load:", confx.errs)

    confx.datax = {}

    if 1: #not confx.datax:
        confx.add("test",   "key",    "val")
        confx.add("test",   "key1",   "val2")
        confx.add("test",   "key2",   "val3")
        confx.add("test",   "key3",   "val4")
        confx.add("test2",  "key1",   "val4")
        confx.add("test2",  "key2",   "val4")
        #print("mod", confx.datax)

    print("save:")
    confx.save("test.ini")


# EOF
