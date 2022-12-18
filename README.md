# pydbase

## High speed database

### Fast data save / retrieve

  The motivation was to create a no frills way of saving / retrieving data fast.
  the command line tester can drive most aspects of this API;


## API

    The module 'twincore' uses two data files and a lock file. The file names are generated
    from the base name of the data file. .pidx for the index, .lock for the lock file.
    The lock file times out in xx seconds and breaks the lock. (in case of frozen process)

## The test executable

    The file pydbase.py exercises most of the twincore functionality. Here is the help screen to drive it.

          Usage: pydebase.py [options]
          Options: -h         help (this screen)
                   -V         print version        ||  -q      quiet on
                   -d         debug level (unused) ||  -v      verbosity on
                   -r         write random data    ||  -w      write record(s)
                   -z         dump backwards(s)    ||  -i      show deleted record(s)
                   -f  file   input or output file (default: 'first.pydb')
                   -n  num    number of records to write
                   -g  num    get number of records
                   -p  num    skip number of records on get
                   -l  lim    limit number of records on get
                   -x  max    limit max number of records to get
                   -k  key    key to save (quotes for multi words)
                   -a  str    data to save (quotes for multi words)
                   -y  key    find by key
                   -t  key    retrieve by key
                   -o  offs   get data from offset
                   -e  offs   delete at offset
                   -u  rec    delete at position
        The default action is to dump records to screen in reverse order.


Comparison to other databases:

 This comparison is to show the time it takes to write 500 records.
In the tests the record size is about the same (Hello /vs/ "111 222")
Please see the sqlite_test.sql for details of data output;

The test can be repeated with running the 'time.sh' script file.
Please note the the time.sh clears all files tests/* for a fair test.

        sqlite time test, 500 records ...
        real	0m1.537s
        user	0m0.025s
        sys	0m0.050s
        pydbase time test, 500 records ...
        real	0m0.149s
        user	0m0.143s
        sys	0m0.004s

  Please mind the fact that the sqlite engine has to do a lot of parsing which we
skip doing; That is why pydbase is an order of magnitude faster ...

### TODO

    Speed up by implementing this a 'C' module

Work in progress ....

