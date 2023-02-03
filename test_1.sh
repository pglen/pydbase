#!/bin/bash

mkdir -p data
rm -f data/*
echo -n "Creating data ... "
for aa in  {1..5}
do
    ./pydbase.py -w
done
echo "OK"
./pydbase.py $1
