#!/usr/bin/env python

"""
Have a folder with all the variants in it:

test_dirs/
    test1/
        /src
        /dest

dup the test_dirs folder somewhere so I can rm -rf at end for cleanup

test1 - no dest exists
test2 - directories in sync
test3 - extra files in src
test4 - extra files in dest
test5 - extra files in both

Test design:

00. Call each one with no parms, missing parms, invalid parms, switches
10. Rename store
13. Remove store
16. Create a second brstores.json
17. Test everything using the -j override
18. Test debug flag
19. Test pv flag
20. Add all the stores for the backup/restore operations
20a. Unzip the test_dirs.zip into the temp/backup and temp/restore areas
20b. Unzip the test_dirs_backup.zip into temp/results/backup
20c. Unzip the test_dirs_restore.zip into temp/results/restore
21a. Test backup test1
21b. Test backup test2
21c. Test backup test3
21d. Test backup test4
21e. Test backup test5
21f. Test restore test1
21g. Test restore test2
21h. Test restore test3
21i. Test restore test4
21j. Test restore test5
22. Remove all the stores for the backup/restore operations

filecmp the backup/* to temp/results/backup
filecmp the restore/* to temp/results/restore

remove the backup, restore and results folders.

"""

from sys import path
from os.path import dirname, abspath, realpath, split
bin_path, whocares = split(dirname(realpath('__file__')))
lib_path = abspath(bin_path)
path.insert(0, lib_path)


import io
import StringIO
import sys
from unittest import TestCase, TestLoader, TextTestRunner

from brstores import br
from brstores.brstores import SyncError

# TODO: This belongs in pylib
_pushdstack = []

# TODO: this should throw exceptions if it fails.

def parent(pathspec):
    from os.path import split
    path, filename = split(pathspec)

    return path

def pushd(dir=None):
    """Set current working directory to 'dir' and save where we are now on a stack.
    Later you can use popd to restore the original directory"""
    global _pushdstack
    from os import getcwd, chdir

    if dir == None:
        dir = getcwd()

    if not isinstance(dir,type('')):
        return False

    _pushdstack.append(getcwd())

    try:
        chdir(dir)
        err = 0
    except OSError:
        err = 1

    if err == 1:
        _pushdstack.pop()
        return False

    return True

def popd():
    """Set the current working directory back to what it was when pushd was called"""
    global _pushdstack
    from os import chdir

    if len(_pushdstack) == 0:
        return False

    try:
        chdir(_pushdstack.pop())
        err = 0
    except OSError:
        err = 1

    return err == 0


DEFAULT_STORE = './test_brstores.json'
temp_testdir = ''

def setup_testdirs():
    from shutil import copy2
    from os.path import isfile, isdir, join
    from tempfile import mkdtemp, gettempdir

    global temp_testdir
    temp_testdir = mkdtemp(suffix='.test', dir='/var/tmp/')
    testdirs_zip = 'test_dirs.zip'
    testdirs_src = join('.',testdirs_zip)
    testdirs_dest = join(temp_testdir,testdirs_zip)
    #try:
    #    copy2(testdirs_src, testdirs_dest)
    #except OSError as why:
    #    print("Error copying testdirs.zip file: [{}]".format(str(why)))
    #    raise
    from os import system
    system('unzip {} -d {}'.format(testdirs_src, temp_testdir))

def setUpModule():
    print("setup module")
    
    #setup_testdirs()
    
    # remove the temp_brstores.json if it exists (here and teardown)
    # should I remember and reset the default store? Probably...
    from os.path import isfile
    from os import unlink
    if isfile(DEFAULT_STORE):
        unlink(DEFAULT_STORE)
    from brstores import BrStores
    print("Current default JSON file is: {}".format(BrStores().getDefaultJSONStore()))
    BrStores().saveDefaultJSONStore(DEFAULT_STORE)
    pass

def tearDownModule():
    print("teardown module")
    global temp_testdir

    if pushd(parent(temp_testdir)):
        from os import getcwd, system

        # TODO: make this pure python, no rm -rf...
    
        print("Removing {}".format(getcwd()))

        system("echo rm -rf {}".format(temp_testdir))

        popd()
        print("{}".format(getcwd()))
    else:
        print("Unable to chdir to {}".format(parent(temp_testdir)))


class TestBrStoresClass(TestCase):
    @classmethod
    def setUpClass(cls):
        print("setup class")
        pass

    @classmethod
    def tearDownClass(cls):
        print("teardown class")
        pass

    def setUp(self):
        self.capturedOutput = StringIO.StringIO()     # Create StringIO object
        sys.stdout = self.capturedOutput              # Redirect sys.stdout
        sys.stderr = self.capturedOutput
        self.brs = br.BrSync()
        self.brs.testing = True

    def tearDown(self):
        sys.stdout = sys.__stdout__    # Reset redirect.
        sys.stderr = sys.__stderr__
        del self.brs
        self.brs = None
        del self.capturedOutput

    def process(self, which, checkEqual=True):
        with open('run/{}.txt'.format(which), 'w') as mf2:
            mf2.write(self.capturedOutput.getvalue())

        if(checkEqual):
            with open('cmp/{}.txt'.format(which), 'r') as myfile:
                data = myfile.read()
            self.assertEqual(self.capturedOutput.getvalue(), data)

    def test_0_init(self):
        from os import unlink
        from os.path import isfile
        self.brs.run('defaults'.split())
        print("Current JSON store contents (should be empty):")
        self.brs.run(['dump'])      # dump current store, should be empty
        new_store_1 = './test_make_new_store.json'
        new_store_2 = './test_make_new_store_make_default.json'
        self.brs.run('i {}'.format(new_store_1).split())
        print("Newly created JSON store contents:")
        self.brs.run(['dump', '-j', '{}'.format(new_store_1)])
        self.brs.run('defaults'.split())
        self.brs.run('init {} -md'.format(new_store_2).split())
        print("Newly created default JSON store contents:")
        self.brs.run(['dump'])
        self.brs.run('defaults'.split())
        self.brs.run('sdjs {}'.format(DEFAULT_STORE).split())
        print("Previous JSON store contents (should still be empty):")
        self.brs.run(['dump'])
        unlink(new_store_1)
        unlink(new_store_2)
        self.assertEqual(isfile(new_store_1),False)
        self.assertEqual(isfile(new_store_2),False)
        self.process('init')
        
    def test_10_help(self):
        with self.assertRaises(SystemExit):
            self.brs.run(['-h'])

        with self.assertRaises(SystemExit):
            self.brs.run(['--help'])

        help_cmds = ['i -h', 'init --help', 'defaults --help', 
                     'sdjs --help', 'setDefaultJSONstore -h',
                     'b -h', 'bu --help', 'backup -h',
                     'r -h', 're --help', 'restore --help', 
                     'addStore --help', 'as -h', 
                     'updateStore -h', 'us --help', 
                     'rens -h', 'renameStore --help',
                     'renv --help', 'renameVariant -h',
                     'setd -h', 'setDefault --help',
                     'rems --help', 'removeStore -h',
                     'remv -h', 'removeVariant --help',
                     'remd --help', 'removeDefault -h',
                     'dump -h',
        ]
        for help in help_cmds:
            print('{}\n{}\n{}'.format('-'*40, help, '-'*40))
            with self.assertRaises(SystemExit):
                self.brs.run(help.split())
        self.process('help')

    def test_20_addstore(self):
        self.brs.run('as test1 test_dirs/test1/src test_dirs/test1/dest'.split())
        self.brs.run('dump -s test1'.split())
        self.brs.run(['addStore', 'test2', 'src/path/1', 
                      '-f', ' --temp-dir=/temp/dir -h --ipv6 -0 --timeout=25',
                      '-v', 'variant1', 'dest/path/3',
                     ])
        self.brs.run('dump -s test2'.split())
        self.brs.run('as test3 test_dirs/test3a/src test_dirs/test3a/dest -v variant3a'.split())
        self.brs.run('dump -s test3'.split())
        self.brs.run('as -v variant3b test3 test_dirs/test3b/src test_dirs/test3b/dest'.split())
        self.brs.run('dump -s test3'.split())
        self.brs.run('as test3 -v variant3c test_dirs/test3c/src test_dirs/test3c/dest'.split())
        self.brs.run('dump -s test3'.split())
        self.brs.run('as test3 test_dirs/test3d/src -v variant3d test_dirs/test3d/dest'.split())
        self.brs.run('dump -s test3'.split())

        self.process('addstore')

    def test_21_updatestore(self):
        self.brs.run('dump -s test1'.split())
        self.brs.run('us test1 test_dirs/test1/src test_dirs/test1/destNEW'.split())
        self.brs.run('dump -s test1'.split())
        self.brs.run('dump -s test2'.split())
        self.brs.run(['updateStore', 'test2', 'src/path/1/NEW', 
                      '-f', ' --temp-dir=/temp/dir -h --ipv4 -0 --timeout=25',
                      '-v', 'variant1', 'dest/path/3',
                     ])
        self.brs.run('dump -s test2'.split())

        try:
            self.brs.run('us test99 src/willfail dest/betterfail'.split())
        except SyncError as se:
            print("Expected SyncError Exception: {}:{}".format(se.errno,se.errmsg))

        try:
            self.brs.run('us test2 src/willfail dest/betterfail -v variant99'.split())
        except SyncError as se:
            print("Expected SyncError Exception: {}:{}".format(se.errno,se.errmsg))

        self.brs.run(['dump'])

        self.process('updatestore')

    def test_31_variants(self):
        print("test variant logic")
        self.brs.run(['dump'])

        # Invalid / Missing parameter tests
        for sub_command in ['setd', 
                            'setd test3',
                            'setd test3 -v no_switch_for_variant', 
                           ]:
            print("CMD: {}".format(sub_command))
            with self.assertRaises(SystemExit):
                self.brs.run(sub_command.split())

        # Things that will raise exceptions from BrStores()
        for sub_command in ['setd test_not_a_store variant3d', 
                            'setd test3 invalid_variant',
                           ]:
            try:
                self.brs.run(sub_command.split())
            except SyncError as se:
                print("Expected SyncError Exception: {}:{}".format(se.errno,se.errmsg))

        # 7a. Make default variant
        # 7b. Try to make non-existant variant default
        # 9a. Rename variant
        # 9b. Rename default variant, make sure __default__ is updated
        # 9c. Remove default variant, make sure __default__ is removed
        # 9d. Remove variant
        self.process('variants')

    def test_skeleton(self):
        print("this is a skeleton test")
        self.process('skeleton')

    def test_zdump(self):
        self.brs.run('dump'.split())
        self.brs.run('dump -ss'.split())
        self.brs.run('dump -ls'.split())
        self.process('dump')



if __name__ == '__main__':
    suite3 = TestLoader().loadTestsFromTestCase(TestBrStoresClass)
    #suite3.sortTestMethodsUsing = None     # this must be before loadTests...
    TextTestRunner(verbosity=2).run(suite3)
