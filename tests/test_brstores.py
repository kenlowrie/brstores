#!/usr/bin/env python

"""
Unittest for BrStores package

Test design:

20. Add all the stores for the backup/restore operations
20d. Test the -j override with backup and restore...
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

create the real r_res and b_res .zip files

filecmp the backup/* to temp/results/backup
filecmp the restore/* to temp/results/restore

"""

from sys import path
from os.path import dirname, abspath, realpath, split
bin_path, whocares = split(dirname(realpath('__file__')))
lib_path = abspath(bin_path)
path.insert(0, lib_path)


import io
import StringIO
import sys
from os.path import abspath
from unittest import TestCase, TestLoader, TextTestRunner

from brstores import br
from brstores.brstores import SyncError
from pylib import parent, pushd, popd

DEFAULT_STORE = './test_brstores.json'
DEFAULT_BRTEST_STORE = abspath('./test_backup_restore.json')
temp_testdir = ''
testdirs_backup_dir = ''
testdirs_restore_dir = ''
testdirs_backup_results_dir = ''
testdirs_restore_results_dir = ''

def setup_testdirs():
    from shutil import copy2
    from os.path import isfile, isdir, join
    from tempfile import mkdtemp, gettempdir

    global temp_testdir
    temp_testdir = mkdtemp(suffix='.test', dir='/var/tmp/')
    print("Created test directory: {}".format(temp_testdir))
    
    testdirs_zip = 'test_dirs.zip'
    testdirs_backup_results_zip = 'test_dirs_b_results.zip'
    testdirs_restore_results_zip = 'test_dirs_r_results.zip'

    testdirs_src = join('.',testdirs_zip)
    testdirs_b_res_src = join('.', testdirs_backup_results_zip)
    testdirs_r_res_src = join('.', testdirs_restore_results_zip)

    global testdirs_backup_dir, testdirs_restore_dir
    global testdirs_backup_results_dir, testdirs_restore_results_dir

    testdirs_backup_dir = join(temp_testdir, "backup")
    testdirs_restore_dir = join(temp_testdir, "restore")
    testdirs_backup_results_dir = join(temp_testdir, "results", "backup")
    testdirs_restore_results_dir = join(temp_testdir, "results", "restore")

    from os import system, makedirs
    
    makedirs(testdirs_backup_dir)
    makedirs(testdirs_restore_dir)
    makedirs(testdirs_backup_results_dir)
    makedirs(testdirs_restore_results_dir)

    output = './unzip_out.txt'
    print("Unzipping: {} to {}".format(testdirs_src, testdirs_backup_dir))
    system('unzip {} -d {} 1>{} 2>&1'.format(testdirs_src, testdirs_backup_dir, output))

    print("Unzipping: {} to {}".format(testdirs_src, testdirs_restore_dir))
    system('unzip {} -d {} 1>>{} 2>&1'.format(testdirs_src, testdirs_restore_dir, output))

    print("Unzipping: {} to {}".format(testdirs_b_res_src, testdirs_backup_results_dir))
    system('unzip {} -d {} 1>>{} 2>&1'.format(testdirs_b_res_src, testdirs_backup_results_dir, output))

    print("Unzipping: {} to {}".format(testdirs_r_res_src, testdirs_restore_results_dir))
    system('unzip {} -d {} 1>>{} 2>&1'.format(testdirs_r_res_src, testdirs_restore_results_dir, output))

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

def cleanUpTempTestDir(testdir):
    from os import walk, remove, rmdir
    from os.path import join

    for root, dirs, files in walk(testdir, topdown=False):
        for name in files:
            #print('unlink {}'.format(join(root,name)))
            remove(join(root, name))
        for name in dirs:
            #print('rmdir {}'.format(join(root,name)))
            rmdir(join(root, name))

def tearDownModule():
    print("teardown module")
    global temp_testdir

    if pushd(parent(temp_testdir)):
        from os import rmdir, getcwd

        print("CWD = {}".format(getcwd()))
    
        print("Removing {}".format(temp_testdir))

        cleanUpTempTestDir(temp_testdir)
        rmdir(temp_testdir)

        popd()
        print("CWD = {}".format(getcwd()))
    else:
        print("Unable to chdir to {}".format(parent(temp_testdir)))

def separate(message):
    print('{0}\n{1}\n{0}'.format('-' * 42, message))


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
        print("test init JSON data store logic")
        run = lambda cmd: self.brs.run(cmd.split())

        # Invalid / Missing parameter tests
        for sub_command in ['i', 'init']:
            print("CMD: {}".format(sub_command))
            with self.assertRaises(SystemExit):
                separate(sub_command)
                run(sub_command)

        separate('Stuff that should work')
        run('defaults')
        print("Current JSON store contents (should be empty):")
        run('dump')      # dump current store, should be empty
        # First store will be in current working directory
        new_store_1 = './test_make_new_store.json'
        # This store will be put into the brstores/ folder because no path given
        new_store_2 = 'test_make_new_store_make_default.json'
        run('i {}'.format(new_store_1))
        print("Newly created JSON store contents:")
        run('dump -j {}'.format(new_store_1))
        run('defaults')
        run('init {} -md'.format(new_store_2))

        # get the path of the current default JSON store for later
        from brstores import BrStores
        json_path = BrStores().getDefaultJSONStore()
        print(json_path)
        
        print("Newly created default JSON store contents:")
        run('dump')
        run('defaults')
        run('sdjs {}'.format(DEFAULT_STORE))
        print("Previous JSON store contents (should still be empty):")
        run('dump')

        separate('Things that will raise exceptions from BrStores()')
        # Things that will raise exceptions from BrStores()
        for sub_command in ['i {}'.format(new_store_1)]:
            try:
                separate(sub_command)
                run(sub_command)
            except SyncError as se:
                print("Expected SyncError Exception: {}:{}".format(se.errno,se.errmsg))

        from os import unlink
        from os.path import isfile
        for file in [new_store_1, json_path]:
            print("Removing {}".format(file))

        unlink(new_store_1)
        unlink(json_path)
        self.assertEqual(isfile(new_store_1),False)
        self.assertEqual(isfile(json_path),False)
        self.process('init')
        
    def test_10_help(self):
        print("test help logic")
        run = lambda cmd: self.brs.run(cmd.split())
        with self.assertRaises(SystemExit):
            run('-h')

        with self.assertRaises(SystemExit):
            run('--help')

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
                run(help)
        self.process('help')

    def test_20_addstore(self):
        print("test add store logic")
        run = lambda cmd: self.brs.run(cmd.split())

        run('dump')
        # Invalid / Missing parameter tests
        for sub_command in ['as', 'addStore',
                            'as missing_src_and_dest',
                            'as store missing_dest', 
                           ]:
            print("CMD: {}".format(sub_command))
            with self.assertRaises(SystemExit):
                run(sub_command)

        run('as test1 test_dirs/test1/src test_dirs/test1/dest')
        run('dump -s test1')
        self.brs.run(['addStore', 'test2', 'src/path/1', 
                      '-f', ' --temp-dir=/temp/dir -h --ipv6 -0 --timeout=25',
                      '-v', 'variant1', 
                      'dest/path/3',
        ])
        run('dump -s test2')
        run('as test3 test_dirs/test3a/src test_dirs/test3a/dest -v variant3a')
        run('dump -s test3')
        run('as -v variant3b test3 test_dirs/test3b/src test_dirs/test3b/dest')
        run('dump -s test3')
        run('as test3 -v variant3c test_dirs/test3c/src test_dirs/test3c/dest')
        run('dump -s test3')
        run('as test3 test_dirs/test3d/src -v variant3d test_dirs/test3d/dest')
        run('dump -s test3')

        # Things that will raise exceptions from BrStores()
        for sub_command in ['as test1 src/willfail dest/betterfail', 
                            'as test3 src/willfail dest/betterfail -v variant3b',
                           ]:
            try:
                separate(sub_command)
                run(sub_command)
            except SyncError as se:
                print("Expected SyncError Exception: {}:{}".format(se.errno,se.errmsg))

        run('dump')

        self.process('addstore')

    def test_21_updatestore(self):
        print("test update store logic")
        run = lambda cmd: self.brs.run(cmd.split())

        # Invalid / Missing parameter tests
        for sub_command in ['us', 'updateStore',
                            'us just_store',
                            'us just_store and_src_path', 
                           ]:
            print("CMD: {}".format(sub_command))
            with self.assertRaises(SystemExit):
                run(sub_command)

        # Things that will raise exceptions from BrStores()
        for sub_command in ['us test99 src/willfail dest/betterfail', 
                            'us test2 src/willfail dest/betterfail -v variant99',
                           ]:
            try:
                separate(sub_command)
                run(sub_command)
            except SyncError as se:
                print("Expected SyncError Exception: {}:{}".format(se.errno,se.errmsg))

        separate('These things should work.')
        run('dump -s test1')
        run('us test1 test_dirs/test1/src test_dirs/test1/destNEW')
        run('dump -s test1')
        run('dump -s test2')
        self.brs.run(['updateStore', 'test2', 'src/path/1/NEW', 
                      '-f', ' --temp-dir=/temp/dir -h --ipv4 -0 --timeout=25',
                      '-v', 'variant1', 
                      'dest/path/3',
        ])
        run('dump -s test2')

        run('dump')

        self.process('updatestore')

    def test_22_stores(self):
        print("test miscellaneous stores sub commands")
        run = lambda cmd: self.brs.run(cmd.split())

        # Invalid / Missing parameter tests
        for sub_command in ['rens', 'renameStore',
                            'rems', 'removeStore',
                            'rens missing_2nd_store',
                           ]:
            with self.assertRaises(SystemExit):
                separate(sub_command)
                run(sub_command)

        # Things that will raise exceptions from BrStores()
        for sub_command in ['rens no_such_store new_name', 
                            'rems no_such_store',
                           ]:
            try:
                separate(sub_command)
                run(sub_command)
            except SyncError as se:
                print("Expected SyncError Exception: {}:{}".format(se.errno,se.errmsg))

        separate('These things should work.')
        # And here's the stuff that should work.
        run('dump')
        run('renameStore test2 test2_new_name')
        run('dump -s test2_new_name')
        run('removeStore test1')
        run('dump')
        
        self.process('stores')

    def test_31_variants(self):
        print("test variant logic")
        run = lambda cmd: self.brs.run(cmd.split())
        run('dump')

        # Invalid / Missing parameter tests
        for sub_command in ['setd', 
                            'setd test3',
                            'setd test3 -v no_switch_for_variant', 
                            'renv',
                            'renv test3',
                            'renv test3 missing_arguments',
                            'remv',
                            'remv test3',
                           ]:
            print("CMD: {}".format(sub_command))
            with self.assertRaises(SystemExit):
                separate(sub_command)
                run(sub_command)

        # Things that will raise exceptions from BrStores()
        # 7b. Try to make non-existant variant default
        for sub_command in ['setd test_not_a_store variant3d', 
                            'setd test3 invalid_variant',
                            'renv invalid_store_name_test3 variant3a will_not_matter',
                            'renv test3 invalid_variant_name will_not_matter',
                            'remv invalid_store_name variant3a',
                            'remv test3 invalid_variant_name',
                           ]:
            try:
                separate(sub_command)
                run(sub_command)
            except SyncError as se:
                print("Expected SyncError Exception: {}:{}".format(se.errno,se.errmsg))

        separate('These things should work.')
        # 7a. Make default variant
        run('setd test3 variant3d')
        run('dump -s test3')
        # 9a. Rename variant
        run('renv test3 variant3c variant3charlie')
        run('dump -s test3')
        # 9b. Rename default variant, make sure __default__ is updated
        run('renv test3 variant3d variant3delta')
        run('dump -s test3')
        # 9c. Remove default variant, make sure __default__ is removed
        run('remv test3 variant3delta')
        run('dump -s test3')
        # 9d. Remove variant
        run('remv test3 variant3a')
        run('dump -s test3')
        
        run('dump')

        self.process('variants')

    def unlink_if_exists(self, filename):
        from os import unlink
        from os.path import isfile

        if isfile(filename):
            unlink(filename)

    def test_40_setup_br_stores(self):
        separate("setup backup/restore stores")
        run = lambda cmd: self.brs.run(cmd.split())

        self.unlink_if_exists(DEFAULT_BRTEST_STORE)

        run('sdjs {}'.format(DEFAULT_BRTEST_STORE))

        run('as bt1 test1/src test1/dest')
        run('as bt2 test2/src test2/dest -v but2')
        run('as bt3 test3/src test3/dest -v but3')
        run('as bt4 test4/src test4/dest --variant but4')
        run('as bt5 test5/src test5/dest --variant but5')
        run('dump')

        run('as rt1 test1/new test1/src')
        run('as rt2 test2/src test2/dest -v rut2')
        run('as rt3 test3/src test3/dest -v rut3')
        run('as rt4 test4/src test4/dest --variant rut4')
        run('as rt5 test5/src test5/dest --variant rut5')
        run('dump')

        run('sdjs {}'.format(DEFAULT_STORE))
        self.process('brsetup')

    # TODO: Is this being used?
    def dump_to_stdout(self, filename):
        with open(filename, 'r') as fp:
            data = fp.read()

        separate("RSync output")
        print(data)

    def test_41_backup(self):
        separate("backup tests")
        run = lambda cmd: self.brs.run(cmd.split())

        my_output_file = abspath('./rsoe_backup.txt')
        self.unlink_if_exists(my_output_file)
    
        global testdirs_backup_dir
        pushd(testdirs_backup_dir)

        sys.stdin = StringIO.StringIO("y\nY\nYes\nSi\nsi\ny\nY\nYes\nSi\nsi\n")

        run('b -j {} bt1 -rsoe {}'.format(DEFAULT_BRTEST_STORE, my_output_file))

        run('sdjs {}'.format(DEFAULT_BRTEST_STORE))

        run('bu bt2 --redirSOE {}'.format(my_output_file))
        run('backup bt3 -v but3 -rsoe {}'.format(my_output_file))
        run('bu bt4 --variant but4 --redirSOE {}'.format(my_output_file))
        run('backup -rsoe {} -v but5 bt5'.format(my_output_file))

        popd()

        #TODO: why isn't this working? when i later try to read, it fails...
        sys.stdin = sys.__stdin__
        #self.dump_to_stdout(my_output_file)
        run('sdjs {}'.format(DEFAULT_STORE))

        self.process('backup')

    def test_42_restore(self):
        separate("restore tests")
        run = lambda cmd: self.brs.run(cmd.split())
        
        my_output_file = abspath('./rsoe_restore.txt')
        self.unlink_if_exists(my_output_file)
    
        global testdirs_restore_dir
        pushd(testdirs_restore_dir)

        sys.stdin = StringIO.StringIO("YES\ny\nYes\nSi\nsi")
        #print("read: {}".format(sys.stdin.readline()))

        run('r -j {} rt1 -rsoe {}'.format(DEFAULT_BRTEST_STORE, my_output_file))

        run('sdjs {}'.format(DEFAULT_BRTEST_STORE))

        run('re rt2 --redirSOE {}'.format(my_output_file))
        run('restore rt3 -v rut3 -rsoe {}'.format(my_output_file))
        run('re rt4 --variant rut4 --redirSOE {}'.format(my_output_file))
        run('restore -rsoe {} -v rut5 rt5'.format(my_output_file))

        popd()

        sys.stdin = sys.__stdin__

        run('sdjs {}'.format(DEFAULT_STORE))

        self.process('restore')

    def test_43_teardown_br(self):
        separate("teardown backup/restore tests")
        run = lambda cmd: self.brs.run(cmd.split())
        
        run('sdjs {}'.format(DEFAULT_BRTEST_STORE))
        
        run('sdjs {}'.format(DEFAULT_STORE))

        self.process('brteardown')

    def test_json_data_store_optional(self):
        separate("test json data store optional")
        run = lambda cmd: self.brs.run(cmd.split())

        test_json_store = './test_optional_json_store.json'
        run('dump')
        run('i {}'.format(test_json_store))
        run('dump -j {}'.format(test_json_store))
        run('as json_store json/src json/dest -j {}'.format(test_json_store))
        run('dump -j {}'.format(test_json_store))
        run('dump -j {} -ss'.format(test_json_store))
        run('dump -ss')        

        run('us json_store json/src/UPDATE -j {} json/dest/UPDATE'.format(test_json_store))
        run('dump -j {} -s json_store'.format(test_json_store))
        run('dump -j {} -ss -s json_store'.format(test_json_store))

        run('rens json_store -j {} json_store_RENAME'.format(test_json_store))
        run('dump -j {} -s json_store_RENAME'.format(test_json_store))
        run('dump -j {} -ls -s json_store_RENAME'.format(test_json_store))
        
        run('renv json_store_RENAME def def_RENAME -j {}'.format(test_json_store))
        run('dump -j {} -s json_store_RENAME'.format(test_json_store))
        run('dump -j {} -ls -s json_store_RENAME'.format(test_json_store))

        run('as json_store_RENAME json/src2 json/dest2 -j {} -v NEW_VARIANT'.format(test_json_store))
        run('setd json_store_RENAME NEW_VARIANT -j {}'.format(test_json_store))
        run('dump -j {} -s json_store_RENAME'.format(test_json_store))
        run('dump -j {} -ss -s json_store_RENAME'.format(test_json_store))

        run('remd json_store_RENAME -j {}'.format(test_json_store))
        run('dump -j {} -s json_store_RENAME'.format(test_json_store))
        run('dump -j {} -ss -s json_store_RENAME'.format(test_json_store))

        run('setd json_store_RENAME NEW_VARIANT -j {}'.format(test_json_store))
        run('dump -j {} -s json_store_RENAME'.format(test_json_store))
        run('dump -j {} -ss -s json_store_RENAME'.format(test_json_store))

        run('remv json_store_RENAME NEW_VARIANT -j {}'.format(test_json_store))
        run('dump -j {} -s json_store_RENAME'.format(test_json_store))
        run('dump -j {} -ls -s json_store_RENAME'.format(test_json_store))

        run('rems json_store_RENAME -j {}'.format(test_json_store))
        run('dump -j {}'.format(test_json_store))

        run('sdjs {}'.format(DEFAULT_STORE))
        run('dump')

        from os import unlink
        from os.path import isfile
        unlink(test_json_store)
        self.assertEqual(isfile(test_json_store),False)

        self.process('json')

    def test_pv(self):
        print("test the pv flags")
        run = lambda cmd: self.brs.run(cmd.split())

        def get_io(command):
            # Create StringIO object
            tempIO = StringIO.StringIO()
            # Save current stdout and stderr
            curStdout, curStderr = (sys.stdout, sys.stderr)
            # Redirect to temp IO buffer
            sys.stdout, sys.stderr = (tempIO, tempIO)
            # Run the command
            run(command)
            # Put back stdout, stderr
            sys.stdout, sys.stderr = (curStdout, curStderr)
            
            return tempIO.getvalue()
        
        pv_io = get_io('-pv defaults')

        from re import match
        py_ver = match(r'^(Python Interpreter Version\:)\s+(\d+\.\d+\.\d+)', pv_io)
        self.assertIsNotNone(py_ver)
        self.assertEqual(len(py_ver.groups()), 2)
        self.assertEqual('Python Interpreter Version:', py_ver.group(1))
        print("Python Interpreter Version was returned by -pv flag. OK.")
        
        # Invalid / Missing parameter tests
        for sub_command in []:
            with self.assertRaises(SystemExit):
                separate(sub_command)
                run(sub_command)

        # Things that will raise exceptions from BrStores()
        for sub_command in []:
            try:
                separate(sub_command)
                run(sub_command)
            except SyncError as se:
                print("Expected SyncError Exception: {}:{}".format(se.errno,se.errmsg))

        # And here's the stuff that should work.
        
        self.process('pv')

    def test_skeleton(self):
        separate("this is a skeleton test")
        run = lambda cmd: self.brs.run(cmd.split())

        # Invalid / Missing parameter tests
        for sub_command in []:
            with self.assertRaises(SystemExit):
                separate(sub_command)
                run(sub_command)

        # Things that will raise exceptions from BrStores()
        for sub_command in []:
            try:
                separate(sub_command)
                run(sub_command)
            except SyncError as se:
                print("Expected SyncError Exception: {}:{}".format(se.errno,se.errmsg))

        # And here's the stuff that should work.
        separate('These things should work.')
        
        self.process('skeleton')

    def test_zdump(self):
        run = lambda cmd: self.brs.run(cmd.split())
        run('dump')
        run('dump -ss')
        run('dump -ls')
        self.process('dump')



if __name__ == '__main__':
    suite3 = TestLoader().loadTestsFromTestCase(TestBrStoresClass)
    #suite3.sortTestMethodsUsing = None     # this must be before loadTests...
    TextTestRunner(verbosity=2).run(suite3)
