#!/usr/bin/env python3

import logging

logging.basicConfig(format='%(module)s:%(levelname)s:%(message)s')


"""
TODO:
    Make pylib a site package, and put it in GitHub, and install as site package.
    Implement the unittests for it
    Write the docstrings
    Add ability to override the underlying message() formatter with my own; i.e.
        pass it in when the object is constructed.
    Add logging
    Review the return code crap, and see if they can be eliminated in favor of just doing exception handling
    Move this into GitHub.
    Package this too, and rely on the pylib package. Once that works, apply this
        to the avscript app.

    Need a switch to show the current brstores.default
    I need to make pylib a dependency from github, but figure out how to
    do this and have it honor the versioning, etc. Otherwise, it won't know
    to update it when I pip install update, right? Figure this out.

"""

from brstores import BrStores, SyncError, message, me

class BrSync(object):
    def __init__(self):
        from argparse import ArgumentParser

        # Define the main parser first
        self._parser = ArgumentParser(prog="br",
                                      description='Sync Directories aka poor man\'s backup and restore',
                                      epilog='Get help on operations by using {} operation -h'.format(me.alias()))
        # Since each parser has an assigned function pointer, we want to provide one for the top level
        # as well. That way, if the user invokes without any subcommands (operations), we can just
        # handle the global flags being set.
        self._parser.set_defaults(func=self.debug)
        # These options are global to all operations
        self._parser.add_argument('-d', '--debug', help='enable debug logging', action="store_true")
        self._parser.add_argument('-pv', '--pyVersionStr', help="show version of Python interpreter.", action="store_true")

        # Define the top level subparsers next.
        json_store_parser = ArgumentParser(add_help=False)
        json_store_parser.add_argument('jsonfile', help='name of json store repository')
        json_store_parser.add_argument('-md', '--makedefault', help='make this the default json store repository', action="store_true")

        json_store_opt_parser = ArgumentParser(add_help=False)
        json_store_opt_parser.add_argument('-j', '--jsonfile', help='name of json store repository', action="store", default="brstores.json")

        store_parser = ArgumentParser(add_help=False, parents=[json_store_opt_parser])
        store_parser.add_argument('store', help='name of data store')

        store_opt_parser = ArgumentParser(add_help=False, parents=[json_store_opt_parser])
        store_opt_parser.add_argument('-s', '--store', help='data store to dump')

        variant_parser = ArgumentParser(add_help=False)
        variant_parser.add_argument('variant', help='name of variant')

        var_opt_parser = ArgumentParser(add_help=False)
        var_opt_parser.add_argument('-v', '--variant', help='data store variant name')

        # And now define the 2nd level subparsers (these rely on top level subparsers)
        set_def_jsonstore_parser = ArgumentParser(add_help=False)

        addstore_parser = ArgumentParser(add_help=False, parents=[store_parser, var_opt_parser])
        addstore_parser.add_argument('srcPath', help='source path of data store')
        addstore_parser.add_argument('destPath', help='destination path of data store')
        addstore_parser.add_argument('-f', '--flags', help='the rsync flags', default="", nargs="?", const="")

        renstore_parser = ArgumentParser(add_help=False, parents=[json_store_opt_parser])
        renstore_parser.add_argument('curStoreName', help='current store name')
        renstore_parser.add_argument('newStoreName', help='new store name')

        renvariant_parser = ArgumentParser(add_help=False, parents=[store_parser])
        renvariant_parser.add_argument('curVariantName', help='current variant name')
        renvariant_parser.add_argument('newVariantName', help='new variant name')
    
        dump_parser = ArgumentParser(add_help=False)
        dump_parser.add_argument('-ss', '--short', help="short summary information only", action="store_true")
        dump_parser.add_argument('-ls', '--long', help="long summary information only", action="store_true")

        # Now add all the subparsers to the main parser
        subparsers = self._parser.add_subparsers(title="operations", dest="operation", description="valid operations", metavar='{i,sdjs,b,r,as,us,rens,renv,setd,rems,remv,remd,dump}')

        subparsers.add_parser('i', 
                              parents=[json_store_parser], 
                              help='initialize a JSON store repository. synonyms: init').set_defaults(func=self.init)
        subparsers.add_parser('init', 
                              parents=[json_store_parser]).set_defaults(func=self.init)

        subparsers.add_parser('sdjs', 
                              parents=[json_store_parser], 
                              help='set def JSON store repo. synonyms: setDefaultJSONstore').set_defaults(func=self.sdjs)
        subparsers.add_parser('setDefaultJSONstore', 
                              parents=[json_store_parser]).set_defaults(func=self.sdjs)

        subparsers.add_parser('b', 
                              parents=[store_parser, var_opt_parser], 
                              help='perform a backup. synonyms: bu, backup').set_defaults(func=self.backup)
        subparsers.add_parser('bu', 
                              parents=[store_parser, var_opt_parser]).set_defaults(func=self.backup)
        subparsers.add_parser('backup', 
                              parents=[store_parser, var_opt_parser]).set_defaults(func=self.backup)

        subparsers.add_parser('r', 
                              parents=[store_parser, var_opt_parser], 
                              help='perform a restore. synonyms: re, restore').set_defaults(func=self.restore)
        subparsers.add_parser('re', 
                              parents=[store_parser, var_opt_parser]).set_defaults(func=self.restore)
        subparsers.add_parser('restore', 
                              parents=[store_parser, var_opt_parser]).set_defaults(func=self.restore)

        subparsers.add_parser('as', 
                              parents=[addstore_parser], 
                              help='add a new store. synonyms: addStore').set_defaults(func=self.addStore)
        subparsers.add_parser('addStore', 
                              parents=[addstore_parser]).set_defaults(func=self.addStore)

        subparsers.add_parser('us', 
                              parents=[addstore_parser], 
                              help='update existing store. synonyms: updateStore').set_defaults(func=self.updateStore)
        subparsers.add_parser('updateStore', 
                              parents=[addstore_parser]).set_defaults(func=self.updateStore)

        subparsers.add_parser('rens', 
                              parents=[renstore_parser], 
                              help='rename existing store. synonyms: renameStore').set_defaults(func=self.renameStore)
        subparsers.add_parser('renameStore', 
                              parents=[renstore_parser]).set_defaults(func=self.renameStore)

        subparsers.add_parser('renv', 
                              parents=[renvariant_parser], 
                              help='rename existing variant. synonyms: renameVariant').set_defaults(func=self.renameVariant)
        subparsers.add_parser('renameVariant', 
                              parents=[renvariant_parser]).set_defaults(func=self.renameVariant)

        subparsers.add_parser('setd', 
                              parents=[store_parser, variant_parser], 
                              help='set default store variant. synonyms: setDefault').set_defaults(func=self.setDefault)
        subparsers.add_parser('setDefault', 
                              parents=[store_parser, variant_parser]).set_defaults(func=self.setDefault)

        subparsers.add_parser('rems', 
                              parents=[store_parser], 
                              help='remove existing store. synonyms: removeStore').set_defaults(func=self.removeStore)
        subparsers.add_parser('removeStore', 
                              parents=[store_parser]).set_defaults(func=self.removeStore)

        subparsers.add_parser('remv', 
                              parents=[store_parser, variant_parser], 
                              help='remove existing variant. synonyms: removeVariant').set_defaults(func=self.removeVariant)
        subparsers.add_parser('removeVariant', 
                              parents=[store_parser, variant_parser]).set_defaults(func=self.removeVariant)

        subparsers.add_parser('remd', 
                              parents=[store_parser], 
                              help='remove default store variant. synonyms: removeDefault').set_defaults(func=self.removeDefault)
        subparsers.add_parser('removeDefault', 
                              parents=[store_parser]).set_defaults(func=self.removeDefault)

        subparsers.add_parser('dump',
                              parents=[dump_parser, store_opt_parser],
                              help='dump the stores JSON file or the named store').set_defaults(func=self.dump)

        self.args = None

    @property
    def args(self):
        return self._args

    @args.setter
    def args(self, args):
        self._args = args

    def _se_exception(self, se):
        logging.error("{}:{}".format(se.errno, se.errmsg))
        return se.errno

    def debug(self):
        logging.debug("debug:{}".format(self.args))

    def init(self):
        logging.debug("init:{}".format(self.args))
        try:
            return BrStores().initialize(self.args.jsonfile, self.args.makedefault)
        except SyncError as se:
            return self._se_exception(se)
        
    def sdjs(self):
        logging.debug("sdjs:{}".format(self.args))
        try:
            return BrStores().saveDefaultStore(self.args.jsonfile)
        except SyncError as se:
            return self._se_exception(se)
        
    def backup(self):
        logging.info("backup:{}".format(self.args))
        return BrStores(self.args.jsonfile).syncOperation(self.args.store, self.args.variant)
        
    def restore(self):
        logging.info("restore:{}".format(self.args))
        return BrStores(self.args.jsonfile).syncOperation(self.args.store,
                                                          self.args.variant,
                                                          False)

    def _as(self,updateStore):
        logging.info("_as:({}):{}".format(updateStore,self.args))
        variantName = self.args.variant if self.args.variant is not None else "def"

        return BrStores(self.args.jsonfile).addStore(self.args.store,
                                                     self.args.srcPath,
                                                     self.args.destPath,
                                                     self.args.flags,
                                                     variantName,
                                                     updateStore)

    def addStore(self):
        logging.info("addStore:{}".format(self.args))
        try:
            return self._as(False)
        except SyncError as se:
            return self._se_exception(se)

    def updateStore(self):
        logging.info("updateStore:{}".format(self.args))
        return self._as(True)
                
    def renameStore(self):
        logging.info("renameStore:{}".format(self.args))
        try:
            return BrStores(self.args.jsonfile).renameStore(self.args.curStoreName, self.args.newStoreName)
        except SyncError as se:
            return self._se_exception(se)
    
    def renameVariant(self):
        logging.info("renameVariant:{}".format(self.args))
        try:
            return BrStores(self.args.jsonfile).renameVariant(self.args.store,
                                                              self.args.curVariantName,
                                                              self.args.newVariantName)
        except SyncError as se:
            return self._se_exception(se)
    
    def setDefault(self):
        logging.info("setDefault:{}".format(self.args))
        try:
            return BrStores(self.args.jsonfile).setDefault(self.args.store,
                                                           self.args.variant)
        except SyncError as se:
            return self._se_exception(se)
        
    def dump(self):
        logging.info("dump:{}".format(self.args))
        brstores = BrStores(self.args.jsonfile)
        
        try:
            if( self.args.store == None ):
                return brstores.dump(self.args.short, self.args.long)

            return brstores.dumpStore(self.args.store, self.args.short, self.args.long)
        except SyncError as se:
            return self._se_exception(se)
        
    def removeStore(self):
        logging.info("removeStore:{}".format(self.args))
        try:
            return BrStores(self.args.jsonfile).removeStore(self.args.store)
        except SyncError as se:
            return self._se_exception(se)        
        
    def removeVariant(self):
        logging.info("removeVariant:{}".format(self.args))
        try:
            return BrStores(self.args.jsonfile).removeVariant(self.args.store, self.args.variant)
        except SyncError as se:
            return self._se_exception(se)

    def removeDefault(self):
        logging.info("removeDefault:{}".format(self.args))
        try:
            return BrStores(self.args.jsonfile).removeDefault(self.args.store)
        except SyncError as se:
            return self._se_exception(se)
        

    def parse_args(self,arguments=None):
        self.args = self._parser.parse_args(None if arguments is None else arguments)
        if(self.args.pyVersionStr):
            message(me.pyVersionStr(),False)

        if self.args.debug:
            logging.getLogger().setLevel(logging.DEBUG)

        return self.args.func

    def run(self, arguments=None):
        self.parse_args(arguments)()

def brsync_command_line(arguments=None):
    brs = BrSync()
    
    brs.run(arguments)

def brsync_runtests(arguments=None):
    logging.getLogger().setLevel(logging.INFO)
    logging.info("Running a bunch of test argument parsing...")

    brs = BrSync()

    if(arguments is not None):
        brs.parse_args(arguments)

    argument_list = [
        'backup mystore',
        'b mystore',
        'bu mystore',
        'b mystore -v myvariant',
        'restore mystore',
        'r mystore',
        're mystore',
        'r mystore -v myvariant',
        'r mystore -v myvariant -j my.json',
        'as mystore srcpath destpath',
        'addStore mystore srcpath destpath -v myvariant',
        '-d -pv addStore mystore srcpath destpath -v myvariant',
        'us mystore srcpath destpath',
        'updateStore mystore srcpath destpath2',
        'setd mystore myvariant',
        'rens curstore newstore',
        'renv store curvariant newvariant',
        'remd mystore',
        'remv store myvariant',
        'rems store',
        'dump -s cl -ss',
        'dump -s store -ls',
        'dump -ls',
        'dump',
        
    ]
    from pprint import pformat
    for argset in argument_list:
        brs.parse_args(argset.split())
        logging.info("ARGSET: ({}):\n{}\n".format(argset, pformat(brs.args.__dict__)))

def brsync_entry():
    from sys import argv
    if(len(argv) > 1):
        if(argv[1].lower() in ['-t', '--test']):
            brsync_runtests()
        else:
            brsync_command_line(argv[1:])
    else:
        message("usage: br [-h | --help] [-t | --test] command [options ...]", False)

    return 0

if __name__ == '__main__':
    from sys import exit
    exit(brsync_entry())
