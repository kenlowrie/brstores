#!/usr/bin/env python3

"""
Simple directory synchronizer based on rsync

This module implements a directory synchronizer which is based on the
rsync command. It can be used to synchronize the contents of two directories,
which you would like to keep mirrored.
"""

from os import system
from os.path import isdir, abspath
from sys import argv, exit, stdin

import pylib

def context():
    """returns the context object for this script."""

    try:
        myself = __file__
    except NameError:
        myself = argv[0]

    return pylib.context(myself)

me = context()

def message(msgstr): print('%s: %s' % (me.alias(), msgstr))

class RSync:
    """This class abstracts the rsync wrapper"""
    def __init__(self, source, destination, flags, ctx=None, redir=None):
        self.source = source
        self.destination = destination
        self.flags = flags
        if(ctx != None):  # override the default context
            global me
            me = ctx
        self.redirpath = None if redir is None or not isdir(pylib.parent(redir)) else abspath(redir)

    def get_redir_flags(self):
        return '' if not self.redirpath else '1>>{} 2>&1'.format(self.redirpath)

    def status(self):
        rc = system("rsync -n -va --delete {} {} {} {}".format(self.flags, 
                                                               self.source, 
                                                               self.destination,
                                                               self.get_redir_flags()))

        message("rsync returned %d\r\n" % rc)

        return rc

    def mirror(self):
        rc = system("rsync -va --delete {} {} {} {}".format(self.flags, 
                                                            self.source,
                                                            self.destination,
                                                            self.get_redir_flags()))

        message("rsync returned %d\r\n" % rc)

        return rc

    def query(self, askFirst=True):
        if askFirst:
            self.status()

            message("Do you want to sync [{}] to [{}] using flags [{}]".format(self.source,
                                                                               self.destination,
                                                                               self.flags))

            answer = stdin.readline().strip()

            if answer.lower() not in ["yes", "y", "si"]:
                message("You did not enter YES, you entered [%s]\r\n" % answer)
                return 0

            message("You entered YES, mirroring the data store...")

        else:
            message("Syncing [{}] to [{}] using flags [{}]".format(self.source,
                                                                   self.destination,
                                                                   self.flags))

        return self.mirror()

if __name__ == '__main__':
    message("csync is a library module. Not directly callable.")
    exit(1)
    
