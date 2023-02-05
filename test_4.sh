#!/bin/bash

# Start a lot of processes (test pydbase)

mkdir -p data
rm -f data/*

for aa in  {1..100}
do
    ./test_3.sh &
done
