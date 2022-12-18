#!/bin/bash

# Create two sets of databases, populate and time the creation

mkdir -p tests
rm -f tests/*;

echo -n "sqlite time test, writing 500 records ... "
time sqlite3 tests/sqlite_test.db < sqlite_test.sql

echo -n "pydbase time test, writing 500 records ... "
time ./pydbase.py -w -n 100 -f tests/pydb_test.pydb

# EOF
