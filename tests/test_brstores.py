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

1. Init a new brstores.json - make default
2. Init a new brstores.json - do not make default
3. Make brstores2.json the default
4. Dump it
5. Add a store
6. Add variants
7. Make default variant
8. Test default variant backup - NOT HERE, LATER
9. Rename variant
10. Rename store
11. Remove default variant
12. Remove variant
13. Remove store
14. Dump stores
15. Dump specific store
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

    print("pushing: {}".format(dir))
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
    setup_testdirs()
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

    pushd(parent(temp_testdir))
    from os import getcwd, system

    # TODO: make this pure python, no rm -rf...
    
    print("{}".format(getcwd()))

    system("echo rm -rf {}".format(temp_testdir))

    popd()
    print("{}".format(getcwd()))


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
        self.brs = br.BrSync()

    def tearDown(self):
        sys.stdout = sys.__stdout__    # Reset redirect.
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

    def test_init(self):
        from os import unlink
        from os.path import isfile
        new_store_1 = './test_make_new_store.json'
        new_store_2 = './test_make_new_store_make_default.json'
        self.brs.run('i {}'.format(new_store_1).split())
        self.brs.run('defaults'.split())
        self.brs.run('init {} -md'.format(new_store_2).split())
        self.brs.run('defaults'.split())
        self.brs.run('sdjs {}'.format(DEFAULT_STORE).split())
        unlink(new_store_1)
        unlink(new_store_2)
        self.assertEqual(isfile(new_store_1),False)
        self.assertEqual(isfile(new_store_2),False)
        self.process('init')
        
    def test_help(self):
        with self.assertRaises(SystemExit):
            self.brs.run(['-h'])
        for help in ['i -h', 'b -h', 'r -h', 'as -h', 'dump -h']:
            print('{}\n{}\n{}'.format('-'*40, help, '-'*40))
            with self.assertRaises(SystemExit):
                self.brs.run(help.split())
        self.process('help')

    def test_addstore(self):
        self.brs.run('as test1 test_dirs/test1/src test_dirs/test1/dest'.split())
        self.brs.run('dump -s test1'.split())
        self.process('addstore')
        pass

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
