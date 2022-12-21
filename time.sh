#!/bin/bash

# Create two sets of databases, populate and time the creation

DDD=test_data
mkdir -p $DDD
rm -f $DDD/*;

echo -n "sqlite time test, writing 500 records ... "
time sqlite3 $DDD/sqlite_test.db < sqlite_test.sql

echo -n "pydbase time test, writing 500 records ... "
time ./pydbase.py -w -n 100 -f $DDD/pydb_test.pydb

# EOF
