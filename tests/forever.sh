#!/bin/bash

#cnt=$1
WWW=0.01

while getopts 'w:' opt; do
  case "$opt" in
    w)
      WWW=$OPTARG
      echo "Processing option 'w'" $WWW
      shift
      shift
      ;;

    ?)
      echo -e "Invalid command option."
      echo -e "Usage: $(basename $0) [ -w ] maxlen"
      exit 1
      ;;

   esac
done

cnt=0
while true; do
    echo $1 - pass $cnt
    cnt=$(($cnt + 1))
    $1 $2 $3 $4 $5 $6 $7 $8 $9;
    if  [ "$?" -ne "0" ]; then
        break;
    fi
    sleep $WWW
done

# EOF
