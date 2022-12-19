# pydbase

## High speed database with key / data

### Fast data save / retrieve

  The motivation was to create a no frills way of saving / retrieving data fast.
  the command line tester can drive most aspects of this API;

## API

The module 'twincore' uses two data files and a lock file. The file names are generated
from the base name of the data file. .pidx for the index, .lock for the lock file.
The lock file times out in 0.3 seconds and breaks the lock. (in case of frozen process)

Example db creation:

    core = twincore.TwinCore(deffile)

Setting verbosity and debug level:

    twincore.core_quiet = quiet
    twincore.core_verbose = verbose
    twincore.core_pgdebug = pgdebug
    twincore.core_showdel = sdelx

Some basic ops:

    dbsize = core.getdbsize()

    core.save_data(keyx, datax)
    rec_arr = core.retrieve(keyx, ncount)
    print("rec_arr", rec_arr)

### Structure of the data:

    32 byte header, starting with FILESIG

    4 bytes    4 bytes          4 bytes         Variable
    ------------------------------------------------------------
    RECSIG     Hash_of_key      Len_of_key      DATA_for_key
    RECSEP     Hash_of_payload  Len_of_payload  DATA_for_payload

        .
        .
        .

    RECSIG     Hash_of_key      Len_of_key      DATA_for_key
    RECSEP     Hash_of_payload  Len_of_payload  DATA_for_payload

    where:
    RECSIG="RECB" (record begin here)
    RECSEP="RECS" (record separated here)
    RECDEL="RECX" (record deleted)

    Deleted records are marked with RECSIG mutated from RECB to RECX

      Vacuum will remove the deleted records; Make sure your database has no
    pending ops; or non atomic opts;

        (like: find keys - delete keys in two ops)

      New data is appended to the end, no duplicate filtering is done.
    Retrieval is searched from reverse, the latest record with this key
    is retrieved first. Most of the times this behavior is what people
    want; also the record history is kept this way, also a desirable
    behavior.

## The test executable script:

The file pydbase.py exercises most of the twincore functionality. It also
provides examples of how to drive it.

Here is the help screen of pydebase.py:

        Usage: pydebase.py [options]
          Options: -h         help (this screen)
                   -V         print version        ||  -q      quiet on
                   -d         debug level (0-10)   ||  -v      verbosity on
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
                   -U         Vacuum DB
                   -R         reindex recover DB
        The default action is to dump records to screen in reverse order.

### Comparison to other databases:

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

### Saving more complex data

  The database saves a key / value pair. However, the key can be mutated to contain
meta data. (for example adding a string in front of it.) [like: CUST_  for customer details]
Also the key can be made unique by adding a UUID to it.

  The data can consist of any text / binary. The library pypacker.py can pack any data
into a string; A copy of pypacker is included here.

## pypacker.py

 This module can pack arbitrary python data into a string; which can be used to store
anything in the pydbase data section.

Example from running testpacker.py:

    org: (1, 2, 'aa', ['bb', b'dd'])
    packed: pg s4 'iisa' i4 1 i4 2 s2 'aa' a29 'pg s2 'sb' s2 'bb' b4 'ZGQ=' '
    unpacked: [1, 2, 'aa', ['bb', b'dd']]
    rec_arr: pg s4 'iisa' i4 1 i4 2 s2 'aa' a29 'pg s2 'sb' s2 'bb' b4 'ZGQ=' '
    rec_arr_upacked: [1, 2, 'aa', ['bb', b'dd']]

 There is also the option of using pypacker on the key itself. Because the key
is identified by its hash, there is no speed penalty; Note that the hash is a 32 bit
one; collisions are possible, however unlikely; To compensate, make sure you compare the
key proper with the returned key.

### TODO

    Speed up by implementing this as a 'C' module

# EOF
