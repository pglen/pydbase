#!/bin/bash

rm -f data/*
echo -n "Creating data ... "

for aa in  {1..10}
do
    ./pydbase.py -w -r
done

echo "OK"

./pydbase.py $1
