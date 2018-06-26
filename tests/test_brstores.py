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
8. Test default variant backup
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
20.

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

def setUpModule():
    print("setup module")
    # remove the temp_brstores.json if it exists (here and teardown)
    from brstores import BrStores
    BrStores().saveDefaultStore('./test_brstores.json')
    pass

def tearDownModule():
    print("teardown module")
    pass


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

    def test_help(self):
        with self.assertRaises(SystemExit):
            self.brs.run(['-h'])
        for help in ['i -h', 'b -h', 'r -h', 'as -h', 'dump -h']:
            print('{}\n{}\n{}'.format('-'*40, help, '-'*40))
            with self.assertRaises(SystemExit):
                self.brs.run(help.split())
        self.process('help')

    def test_dump(self):
        self.brs.run('dump'.split())
        self.brs.run('dump -ss'.split())
        self.brs.run('dump -ls'.split())
        self.process('dump')



if __name__ == '__main__':
    suite3 = TestLoader().loadTestsFromTestCase(TestBrStoresClass)
    TextTestRunner(verbosity=2).run(suite3)
