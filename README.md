# pydbase

## High speed database with key / data

### Fast data save / retrieve

  The motivation was to create a no frills way of saving / retrieving data
fast. the command line tester can drive most aspects of this API;

NOT ready for production yet.

## API

  The module 'twincore' uses two data files and a lock file. The file
 names are generated from the base name of the data file;
pydb for data; .pidx for the index, .lock for the lock file.
The lock file times out in 0.3 seconds and breaks the lock.
 (in case of frozen process)

Setting verbosity and debug level:

    twincore.core_quiet = quiet
    twincore.core_verbose = verbose
    twincore.core_pgdebug = pgdebug
    twincore.core_showdel = sdelx

    (setting before data creation will display mesages from the construtor)

Example db creation:

    core = twincore.TwinCore(deffile)

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

## The db exersizer executable script 'pydbase.py':

   The file pydbase.py exercises most of the twincore functionality. It also
provides examples of how to drive it.

Here is the help screen of pydebase.py:

        Usage: pydebase.py [options]
          Options: -h         help (this screen)
                   -V         print version        ||  -q   quiet on
                   -d         debug level (0-10)   ||  -v   increment verbosity level
                   -r         write random data    ||  -w   write record(s)
                   -z         dump backwards(s)    ||  -i   show deleted record(s)
                   -U         Vacuum DB            ||  -R   re-index / recover DB
                   -f  file   input or output file (default: 'pydbase.pydb')
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

### Comparison to other databases:

 This comparison is to show the time it takes to write 500 records.
In the tests the record size is about the same (Hello /vs/ "111 222")
Please see the sqlite_test.sql for details of data output;

The test can be repeated with running the 'time.sh' script file.
Please note the the time.sh clears all files test_data/* for a fair test.

    sqlite time test, writing 500 records ...
    real	0m1.606s
    user	0m0.004s
    sys	0m0.073s
    pydbase time test, writing 500 records ...
    real	0m0.034s
    user	0m0.030s
    sys	0m0.004s

  Please mind the fact that the sqlite engine has to do a lot of parsing which we
skip doing; That is why pydbase is more than an order of magnitude faster ...

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
    (Note: the decode returns an array of data; use data[0] to get the original)

  There is also the option of using pypacker on the key itself. Because the key
is identified by its hash, there is no speed penalty; Note that the hash is a 32 bit
one; collisions are possible, however unlikely; To compensate, make sure you compare the
key proper with the returned key.

## PyTest

 The pytest passes with no errors; Run it from the tests/ directory.

 The following (and more) test are created / executed:

        test_bindata.py .                     [  7%]
        test_create.py .....                  [ 46%]
        test_del.py .                         [ 53%]
        test_dump.py .                        [ 61%]
        test_packer.py ..                     [ 76%]
        test_randdata.py .                    [ 84%]
        test_reindex.py .                     [ 92%]
        test_vacuum.py .                      [100%]

## Maintenance

  The DB can rebuild its index and purge all deleted records. In the test utility
the options are:

        ./pydbase.py -U     for vacuum (add -v for verbosity)

  The database is re-built, the deleted entries are purged, the damaged data (if any)
  is saved into a separate file, created with the same base name as the data base,
  with the '.perr' extension.

        ./pydbase.py -R     for re-index

  The index is recreated; as of the current file contents. This is useful if
the index is lost (like copying the data only)

 The command line utility's help response:

Usage: pydebase.py [options] [arg_key arg_data]
 Options: -h        help (this screen)
          -V        print version        -|-  -q  quiet on
          -d        debug level (0-10)   -|-  -v  increment verbosity
          -r        write random data    -|-  -w  write fixed record(s)
          -z        dump backwards(s)    -|-  -i  show deleted record(s)
          -U        Vacuum DB            -|-  -R  reindex / recover DB
          -I        DB Integrity check   -|-  -c  set check integrity flag
          -s        Skip count           -|-  -K  list keys only
          -y  key   find by key          -|-  -t  key    retrieve by key
          -o  offs  get data from offset -|-  -e  offs   delete at offset
          -u  rec   delete at position   -|-  -g  num    get number of recs
          -k  key   key to save          -|-  -a  str    data to save
          -n  num   number of records to write
          -p  num   skip number of records on get
          -l  lim   limit number of records on get
          -x  max   limit max number of records to get
          -f  file  input or output file (default: 'data/pydbase.pydb')
The default action is to dump records to screen in reverse order.
On the command line, use quotes for multi word arguments.

  If there is a data file without the index, the re-indexing is called
 automatically.   In case of deleted data file, pydbase will recognize
 the dangling index and nuke it byr renaming it to
 orgfilename.pidx.dangle ;

  Note about the 'garbage' and 'old_tries' directory ... older stuff I
tried; some are really useful; For instance take a look at the
simplifier: an array of indexes to save offsets and lengths; The
simplifier makes one range out of overlapping or close to each other
ranges. (min. dist=4)

  The database grows with every record added to it. It does not check if
 the particular record already exists. It adds the new record version to
the end; Retrieving starts from the end, and the data retrieved
(for this particular key) is the last record saved. All the other records
of this key are also there in chronological (save) order. Miracle of
record history archived by default.

  To clean the old record history, one may delete all the records with
this same key, except the last one.

### TODO

    Speed this up by implementing this as a 'C' module

; EOF
