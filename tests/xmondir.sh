#!/bin/bash

# Wait for stuff to change, exec $1 $2 ...

while [ 1 ]; do
    echo Started monitor file $2
    inotifywait $2  > /dev/null 2>&1
    #echo Changed exec $1 $2
    $1 $2 $3 $4
    sleep 1
done

