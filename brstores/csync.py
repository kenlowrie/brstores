#!/usr/bin/env python

import os
import sys

import pylib

def context():
    """returns the context object for this script."""

    try:
        myself = __file__
    except NameError:
        myself = sys.argv[0]

    return pylib.context(myself)

me = context()

def message(msgstr): print ('%s: %s' % (me.alias(),msgstr))

class C_Sync:
    """This class abstracts the rsync wrapper"""
    def __init__(self, source, destination, flags,ctx = None):
        self.source = source
        self.destination = destination
        self.flags = flags
        if( ctx != None ):  # override the default context
            global me
            me = ctx
        
    def status(self):
        rc = os.system("rsync -n -va --delete %s %s %s" % (self.flags, self.source, self.destination) )
    
        message("rsync returned %d\r\n" % rc)
    
        return rc
    
    def mirror(self, askFirst=True):
        rc = os.system("rsync -va --delete %s %s %s" % (self.flags, self.source, self.destination) )
    
        message("rsync returned %d\r\n" % rc)
    
        return rc
    
    def query(self):
    
        self.status()
        
        message("Do you want to sync [%s] to [%s] using flags [%s]" % (self.source,self.destination,self.flags))
        
        answer = sys.stdin.readline().strip()

        if answer.lower() not in ["yes", "y", "si"]:
            message("You did not enter YES, you entered [%s]\r\n" % answer)
            return 0

        message("You entered YES, mirroring the data store...")
        
        return self.mirror()
    
if __name__ == '__main__':
    message("csync is a library module. Not directly callable.")
    sys.exit(1)
    
