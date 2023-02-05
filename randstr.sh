#!/bin/bash

# Generate a random sequence of chars on stdout

stringZ="abcdefghigklmnopqrstuvwxyzABCDEFGHIGKLMNOPQRSTUVWXYZ1234567890"

while getopts 'nc:h' opt; do
  case "$opt" in
    n)
      #echo "Processing option 'n'"
      stringZ="abcdefghigklmnopqrstuvwxyzABCDEFGHIGKLMNOPQRSTUVWXYZ1234567890\ ()_+=@#^&"
      ;;

    b)
      echo "Processing option 'b'"
      ;;

    c)
    arg="$OPTARG"
      echo "Processing option 'c'" $arg
      ;;

    h)
      echo "use: randstr [-n] length"
      exit 0
      ;;

    ?)
      echo -e "Invalid command option.\nUsage: $(basename $0) [-a] [-b] [-c arg]"
      exit 1
      ;;
  esac
done

lenx=${#stringZ}

shift "$(($OPTIND -1))"

for aa in $(seq 0 $1)
do
    mmm=$(($RANDOM % $lenx))
    #echo $aa, $mmm
    echo -n -e ${stringZ:$mmm:1}
done

echo