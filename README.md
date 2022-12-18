# pydbase

## High speed database

### Fast data save / retrieve

  The motivation was to create a no frills way of saving / retrieving data fast.
  the command line tester can drive most aspects of this API;


## API

    The module trincore uses two data files and a lock file.


Comparison to other databases:

 This comparison is to show the time it takes to write 500 records.
In the tests the record size is about the same (Hello /vs/ "111 222")
Please see the sqlite_test.sql for details of data output;

The test can be repeated with running the 'time.sh' script file.
Please note the the time.sh clears all data/* for a fair test.

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

    Speed up by implementing this a 'c' module

Work in progress ....
