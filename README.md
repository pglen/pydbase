# pydbase

## High speed database with key / data

#### see: blockchain functions at the end

 &nbsp; The motivation was to create a no frills way of saving / retrieving data.
It is fast, and the time test shows that this is an order of magnitude
faster than most mainstream databases. This is due to the engine's simplicity.
It avoids expensive computations in favor of quickly saving data.

### Fast data save / retrieve

 &nbsp; Mostly ready for production. All tests pass. Please use caution, as this is new.
The command line tester can drive most aspects of this API; and it is somewhat
complete. It is also  good way to see the API / Module in action.

## API

  &nbsp; The module 'twincore' uses two data files and a lock file. The file
 names are generated from the base name of the data file;
name.pydb for data; name.pidx for the index, name.lock for the lock file.
 In case of frozen process the lock file times out in xx seconds
and breaks the lock. If the locking process (id in lockfile) does
not exist, the lock breaks immediately.

Example DB creation:

    core = twincore.TwinCore(datafile_name)

Some basic ops:

    dbsize = core.getdbsize()

    core.save_data(keyx, datax)
    rec_arr = core.retrieve(keyx, ncount)
    print("rec_arr", rec_arr)

Example chain DB creation:

    core = twinchain.TwinChain(datafile_name)
    core.append(keyx, datax)
    recnum = core.getdbsize()
    rec = core.get_payload(recnum)
    print(recnum, rec)

### Setting verbosity and debug level:

    twincore.core_quiet   = quiet
    twincore.core_verbose = verbose
    twincore.core_pgdebug = pgdebug

 (Setting before data creation will display mesages from the construtor)

### Structure of the data:

    32 byte header, starting with FILESIG

    4 bytes    4 bytes          4 bytes         Variable
    ------------------------------------------------------------
    RECSIG     Hash_of_key      Len_of_key      DATA_for_key
    RECSEP     Hash_of_payload  Len_of_payload  DATA_for_payload

        .
        .

    RECSIG     Hash_of_key      Len_of_key      DATA_for_key
    RECSEP     Hash_of_payload  Len_of_payload  DATA_for_payload

    where:

    RECSIG="RECB" (record begin here)
    RECSEP="RECS" (record separated here)
    RECDEL="RECX" (record deleted)

    Deleted records are marked with the RECSIG mutated from RECB to RECX

      Vacuum will remove the deleted records; Make sure your database has no
    pending ops; or non atomic opts when vacuuming;

        (like: find keys - delete keys in two ops)

      New data is appended to the end, no duplicate filtering is done.
    Retrieval is searched from reverse, the latest record with this key
    is retrieved first. Most of the times this behavior is what we
    want; also the record history is kept this way, also a desirable
    behavior.

## Usage:

### The DB exerciser

   The file dbaseadm.py exercises most of the twincore functionality. It also
provides examples of how to drive it.

The command line utility's help response:

     Usage: dbaseadm.py [options] [arg_key arg_data]
       -h         Help (this screen)   -|-  -E         Replace record in place
       -V         Print version        -|-  -q         Quiet on, less printing
       -d         Debug level (0-10)   -|-  -v         Increment verbosity level
       -r         Randomize data       -|-  -w         Write random record(s)
       -z         Dump backwards(s)    -|-  -i         Show deleted record(s)
       -U         Vacuum DB            -|-  -R         Re-index / recover DB
       -I         DB Integrity check   -|-  -c         Set check integrity flag
       -s         Skip to count recs   -|-  -K         List keys only
       -S         Print num recs       -|-  -m         Dump data to console
       -o  offs   Get data from offset -|-  -G  num    Get record by number
       -F  subkey Find by sub str      -|-  -g  num    Get number of recs.
       -k  keyval Key to save          -|-  -a  str    Data to save
       -y  keyval Find by key          -|-  -D  keyval Delete by key
       -n  num    Number of records    -|-  -t  keyval Retrieve by key
       -p  num    Skip number of recs  -|-  -u  recnum Delete at recnum
       -l  lim    Limit get records    -|-  -e  offs   Delete at offset
       -Z  keyval Get record position  -|-  -X  max    Limit recs on delete
       -x  max    Limit max number of records to get (default: 1)
       -f  file   Input or output file (default: 'pydbase.pydb')
    The verbosity / debugl level influences the amount of data presented.
    Use quotes for multi word arguments.

### The chain adm utility:

    Usage: chainadm.py [options]
       Options: -a  data   append data to the end of chain
                -g recnum  get record
                -k reckey  get record by key/header
                -r recnum  get record header
                -d level   debug level
                -n         append / show number of records
                -e         override header
                -t         print record's UUID date)
                -s         skip count
                -x         max record count to list
                -m         dump chain data
                -c         check data integrity
                -i         check link integrity
                -S         get db size
                -v         increase verbosity
                -h         help (this screen)

### Comparison to other databases:

 This comparison is to show the time it takes to write 500 records.
In the tests the record size is about the same (Hello, 1  /vs/ "Hello", 1)
Please see the sqlite_test.sql for details of data output;

 The test can be repeated with running the 'time.sh' script file.
Please note the the time.sh clears all files in test_data/* for a fair test.

    dbaseadm time test, writing 500 records ...
    real	0m0.108s
    user	0m0.068s
    sys	0m0.040s
    chainadm time test, writing 500 records ...
    real	0m0.225s
    user	0m0.154s
    sys	0m0.071s
    sqlite time test, writing 500 records ...
    real	0m1.465s
    user	0m0.130s
    sys	0m0.292s

  Please note that the sqlite engine has to do a lot of parsing which we
skip doing; That is why pydbase is more than an order of magnitude faster ...
even with all the hashing for data integrity check

### Saving more complex data

  The database saves a key / value pair. However, the key can be mutated
to contain more sophisticated data. For example: adding a string in front of it.
[ Like: the string CUST_ for customer data / details]. Also the key can be made
unique by adding a UUID to it, or using pyvpacker to construct it. (see below)

 &nbsp; The data may consist of any text / binary. The library pyvpacker and can pack
any data into a string; It is installed as a dependency, and a copy of
pyvpacker can be obtained from pip or github.

## the pyvpacker.py module:

 This module can pack arbitrary python data into a string; which can be
used to store anything in the pydbase's key / data sections. Note that
data type is limited to the python native data types and compounds thereof.

        Types: (int, real, str, array, hash)

Example from running testpacker.py:

    org: (1, 2, 'aa', ['bb', b'dd'])
    packed: pg s4 'iisa' i4 1 i4 2 s2 'aa' a29 'pg s2 'sb' s2 'bb' b4 'ZGQ=' '
    unpacked: [1, 2, 'aa', ['bb', b'dd']]
    rec_arr: pg s4 'iisa' i4 1 i4 2 s2 'aa' a29 'pg s2 'sb' s2 'bb' b4 'ZGQ=' '
    rec_arr_upacked: [1, 2, 'aa', ['bb', b'dd']]
    (Note: the decode returns an array of data; use data[0] to get the original)

  There is also the option of using pyvpacker on the key itself. Because the key
is identified by its hash, there is no speed penalty; Note that the hash is a 32 bit
one; collisions are possible, however unlikely; To compensate, make sure you compare the
key proper with the returned key.

## Maintenance

  The DB can rebuild its index and purge (vacuum)  all deleted records. In the
test utility the options are:

        ./dbaseadm.py -U     for vacuum (add -v for verbosity)

  The database is re-built, the deleted entries are purged, the damaged data (if any)
  is saved into a separate file, created with the same base name as the data base,
  with the '.perr' extension.

        ./dbaseadm.py -R     for re-index

  The index is recreated; as of the current file contents. This is useful if
the index is lost (like copying the data only)

  If there is a data file without the index, the re-indexing is called
 automatically.   In case of deleted data file, pydbase will recognize
 the dangling index and nuke it by renaming it to
 orgfilename.pidx.dangle (Tue 07.Feb.2023 just deleted it);

  The database grows with every record added to it. It does not check if
 the particular record already exists. It adds the new copy of the record to
the end;
  Retrieving starts from the end, and the data retrieved
(for this particular key) is the last record saved. All the other records
of this key are also there in chronological (save) order. Miracle of
record history archived by default.

  To clean the old record history, one may delete all the records with
this same key, except the last one.

## Blockchain implementation

   The database is extended with a blockhcain implementation. The new class
is called twinchain; and it is a class derived from twincore.

  To drive the blockchain, just use the append method. The database will calculate
all the hashes, integrate it into the existing chain with the new item getting
a backlink field. This field is calculated based upon the previous record's
hash and the previous record's frozen date. This assures that identical data
will have a different hash, so data cannot be anticipated based upon its hash
alone. The hash is done with 256 bits, and assumed to be very secure.

To drive it:

        core = twinchain.TwinChain()    # Takes an optional file name
        core.append("The payload")      # Arbitrary data

    Block chain layer on top of twincore.

        prev     curr
            record
    |   Time Now    |   Time  Now    |  Time Now     |
    |   hash256   | |    hash256   | |   hash256   | |
    |   Header    | |    Header    | |   Header    | |
    |   Payload   | |    Payload   | |   Payload   | |
    |   Backlink  | |    Backlink  | |   Backlink  | |
                  |---->----|      |---->---|     |------ ...

    The hashed sum of fields saved to the next backlink.

## Integrity check

   Two levels; Level one is checking if the record checksums are correct;
   Level two checks if the linkage is correct.

## The in-place update

  The save operation has a flag for in-place update. This is useful for updating
without the data storage extending. Useful for counts and timers. The in-place
update operates as a record overwrite, and has to be equal length than the existing
record. If shorter, the record is padded to the original data's length by appending
spaces. Below is an example to update a counter in the database, which will execute
in a microsecond time range.

    dbcore = twinchain.TwinCore(filename)
    rec = dbcore.get_rec(xxx)
    # Increment count:
    arr = self.packer.decode_data(rec[1])[0]
    arr[0] = "%05d" % (int(arr[0]) + 1)
    strx = str(self.packer.encode_data("", arr))
    ret = dbcore.save_data(rec[0], strx, True)

 If the new data (relativeto the in-place data) is longer, a new record is
created, just like a normal operation. This new, longer record than accommodates all the new in-place requests.
It is recommended that one produces a fixed record size for consistent results.
(See: sprintf (python % operator) in the example above.)

## PyTest

 The pytest passes with no errors;
 The following (and more) test are created / executed:

### Test results:

    ============================= test session starts ==============================
    platform linux -- Python 3.10.12, pytest-7.4.3, pluggy-1.0.0
    rootdir: /home/peterglen/pgpygtk/pydbase
    collected 44 items

    test_acreate.py ...                                                      [  6%]
    test_bigdata.py .                                                        [  9%]
    test_bindata.py .                                                        [ 11%]
    test_chain.py .                                                          [ 13%]
    test_chain_data.py .                                                     [ 15%]
    test_chain_link.py ..                                                    [ 20%]
    test_del.py .                                                            [ 22%]
    test_dump.py .                                                           [ 25%]
    test_find.py ..                                                          [ 29%]
    test_findrec.py ..                                                       [ 34%]
    test_getoffs.py ...                                                      [ 40%]
    test_getrec.py .                                                         [ 43%]
    test_handles.py .....                                                    [ 54%]
    test_inplace.py ...                                                      [ 61%]
    test_integrity.py .                                                      [ 63%]
    test_list.py ..                                                          [ 68%]
    test_lockrel.py .                                                        [ 70%]
    test_multi.py ..                                                         [ 75%]
    test_packer.py ......                                                    [ 88%]
    test_reindex.py .                                                        [ 90%]
    test_search.py ...                                                       [ 97%]
    test_vacuum.py .                                                         [100%]

    ============================== 44 passed in 0.57s ==============================

## History

    1.1         Tue 20.Feb.2024     Initial release
    1.2.0       Mon 26.Feb.2024     Moved pip home to pydbase/
    1.4.0       Tue 27.Feb.2024     Addedd pgdebug
    1.4.2       Wed 28.Feb.2024     Fixed multiple instances
    1.4.3       Wed 28.Feb.2024     ChainAdm added
    1.4.4       Fri 01.Mar.2024     Tests for chain functions
    1.4.5       Fri 01.Mar.2024     Misc fixes
    1.4.6       Mon 04.Mar.2024     Vacuum count on vacuumed records
    1.4.7       Tue 05.Mar.2024     In place record update
    1.4.8       Sat 09.Mar.2024     Added new locking mechanism
    1.4.9       Mon 01.Apr.2024     Updated to run on MSYS2, new locking
    1.5.0       Tue 02.Apr.2024     Cleaned, pip upload
    1.5.1       Wed 10.Apr.2024     Dangling lock .. fixed
    1.6.0       Thu 25.Apr.2024     Added IDX pre and post callbacks
    1.6.1       Mon 29.Apr.2024     D: option corrected

// EOF
