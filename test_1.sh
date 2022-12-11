#!/bin/bash

rm data/first.pydb
echo -n "Creating data ... "

for aa in  {1..10}
do
    ./pydbase.py -w
done

echo "OK"

./pydbase.py
