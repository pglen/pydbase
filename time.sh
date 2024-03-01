#!/bin/bash

# Create two sets of databases, populate and time the creation

DDD=test_data
mkdir -p $DDD
rm -f $DDD/*;

echo -n "dbaseadm time test, writing 500 records ... "
time ./dbaseadm.py -k "Hello, 1" -a "1" -n 500 -f $DDD/pydb_test.pydb

echo -n "chainadm time test, writing 500 records ... "
time ./chainadm.py -a "Hello, 1 " -n 500 -f $DDD/chain_test.pydb

echo -n "sqlite time test, writing 500 records ... "
time sqlite3 $DDD/sqlite_test.db < sqlite_test.sql

# this ls shows you data size efficiency
#ls -l $DDD

# (un) Comment this if you want to see / hide the data
rm -f $DDD/*;

# EOF
