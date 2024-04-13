#!/usr/bin/env python3

# python 3.x
from configparser import ConfigParser
config = ConfigParser()

config.read('config.ini')

sec = config.sections()
#print(sec)

for aa in sec:
    bb = config.items(aa)
    print(aa, ":")
    for cc in bb:
            print("    ", cc[0], "=", cc[1])

if "main" not in sec:
    config.add_section('main')

config.set('main', 'key1', 'value1')
config.set('main', 'key2', 'value2')
config.set('main', 'key3', 'value3')

vvv = config.get('main', 'key4')
config.set('main', 'key4', str(int(vvv)+1))

if "test" not in sec:
    config.add_section('test')

config.set('test', 'data1', 'value1')
config.set('test', 'data2', 'value2')
config.set('test', 'data3', 'value3')

with open('config.ini', 'w') as f:
    config.write(f)

