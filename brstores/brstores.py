#!/usr/bin/env python3

"""
This class implements the BrStores class, which provides simple
syncrhonization logic for doing backup/restore operations at the 
directory level. 

It maintains maintains a dictionary of entries in the following
format to keep track of data stores:

    storename: { 
        variationName: { src: "", dest: "", flags: ""}[,]
        [variantName2: { src: "", dest: "", flags: ""}, ...]
        [__default__: "defaultvariantname"]
    }


TODO:

Need a way to timestamp or identify revision to help prevent out of sync issues
"""

import logging

import kenl380.pylib as pylib


# The class implementation for the exception handling in the underlying classes
class Error(Exception):
    """Base exception class for this module."""
    pass

class SyncError(Error):
    """Various exceptions raised by this module."""
    def __init__(self, errno, errmsg):
        self.errno = errno
        self.errmsg = errmsg


def context():
    """returns the context object for this script."""

    try:
        myself = __file__
    except NameError:
        from sys import argv
        myself = argv[0]

    return pylib.context(myself)

me = context()

def message(msgstr, prefix=True):
    if(prefix):
        print('{}: {}'.format(me.alias(), msgstr))
    else:
        print(msgstr)


class BrStores(object):
    DEF_VARIANT_KEY = "__default__"
    DEF_JSON_STORE = "brstores.json"
    DEF_STORE_KEY = "defaultstore"

    def __init__(self, storeName=None):
        from os.path import isfile, join

        self.defaults_basefilename = join(me.whereami(),"brstores.default")
        self.defaults = self._loadDefaults()
        self.storeName = storeName if storeName is not None and isfile(storeName) else self.__getDefaultStore()
        self.brstores = self._loadStores()

    def __getDefaultStore(self):
        base_filename = BrStores.DEF_JSON_STORE if BrStores.DEF_STORE_KEY not in self.defaults else self.defaults[BrStores.DEF_STORE_KEY]
        return base_filename

    def _loadJSON(self, base_filename):
        from json import load
        dict = {}
        try:
            with open(base_filename, 'r') as fp:
                dict = load(fp)
                fp.close()
        except IOError:
            dict = {}

        return dict

    def _saveJSON(self, base_filename, data):
        from json import dump
        try:
            with open(base_filename, 'w') as fp:
                dump(data, fp, indent=4)
                fp.close()
        except IOError:
            return -1
            
        return 0

    def _loadDefaults(self):
        return self._loadJSON(self.defaults_basefilename)

    def _saveDefaults(self):
        return self._saveJSON(self.defaults_basefilename, self.defaults)

    def _loadStores(self):
        return self._loadJSON(self.storeName)
        
    def _saveStores(self):
        return self._saveJSON(self.storeName, self.brstores)

    def _fixSrcDestPaths(self, store):
        """Make sure that src has a trailing slash, and dest does not!"""

        from sys import _getframe
        fn = _getframe().f_code.co_name

        if (store == None): return store

        logging.debug("{}:src={} dest={}".format(fn, store['src'], store['dest']))

        if (store['src'][-1] != '/'): store['src'] += '/'
        if (store['dest'][-1] == '/'): store['dest'] = store['dest'][0:-1]

        logging.debug("{}:src={} dest={}".format(fn, store['src'], store['dest']))

        return store
    
    def _getStores(self):
        """Return a list of the data stores in the dictionary."""
        
        return self.brstores.keys()

    def _getVariant(self,which,variant):
        if which in self._getStores():
            if variant in self.brstores[which]:
                message("Located variant [{}] in store [{}] ...".format(variant, which))
                return self.brstores[which][variant]
            
            message("Variant [{}] not found for store [{}]".format(variant, which))
            return None
            
        message("No store named [{}] found!".format(which))
        return None

    def _getDefaultVariant(self, which):
        if which in self._getStores():
            if (BrStores.DEF_VARIANT_KEY in self.brstores[which]):
                message("Default variant is [{}] ...".format(self.brstores[which][BrStores.DEF_VARIANT_KEY]))
                return self.brstores[which][self.brstores[which][BrStores.DEF_VARIANT_KEY]]

            if len(self.brstores[which]) == 1:
                message("Only 1 variant here [{}], so using it...".format(list(self.brstores[which].keys())[0]))
                return self.brstores[which][list(self.brstores[which].keys())[0]]

            message("No default variant and more than one variant for store [{}]".format(which))
            return None

        message("No store named [{}] found!".format(which))
        return None

    def _getTargetSrcDest(self,which,variant,isBackup=True):
        """Get the data store with src, dest and flags for 'which'."""
        
        if which in self._getStores():
            if (variant == None):
                store = self._getDefaultVariant(which)
            else:
                store = self._getVariant(which,variant)

            if (store == None): raise SyncError(5,"Invalid store or variant")

            if (isBackup == True): return store

            message("RESTORE operation, flipping SRC and DEST...")
            tmpSrc = store['src']
            store['src'] = store['dest']
            store['dest'] = tmpSrc

            return store

        raise SyncError(6,"I don't know about any store named [{}]...".format(which))

        return None

    def saveDefaultJSONStore(self, newDefaultStore):
        from os.path import split, isdir, abspath

        dir,name = split(newDefaultStore)
        if dir and not isdir(dir):
            raise SyncError(4, "[{}] JSON store path doesn't exist.".format(dir))

        self.defaults[BrStores.DEF_STORE_KEY] = abspath(newDefaultStore)
        message("Setting default store to {}".format(self.defaults[BrStores.DEF_STORE_KEY]))

        return self._saveDefaults()

    def getDefaultJSONStore(self):
        if BrStores.DEF_STORE_KEY in self.defaults:
            return self.defaults[BrStores.DEF_STORE_KEY]

        return ''

    def dumpDefaults(self):
        message("\nCurrent defaults set in {}\n".format(self.defaults_basefilename), False)
        for item in self.defaults:
            message("\t{}: {}".format(item, self.defaults[item]), False)

        message("", False)
        return 0

    def syncOperation(self, storeName, variantName, isBackup=True, redirsoe=None, noPrompt=False):
        operStr = "backup" if isBackup else "restore"

        store = self._fixSrcDestPaths(self._getTargetSrcDest(storeName,variantName,isBackup))

        from .csync import RSync

        if not noPrompt:
            message("Dry run: src={} dest={} flags={}".format(store['src'],store['dest'],store['flags']))
    
        cs = RSync(store['src'],store['dest'],store['flags'],me, redirsoe)
    
        return cs.query(askFirst=not noPrompt)
        
    def addStore(self,store,src,dest,flags,variant,update):
        if(variant == BrStores.DEF_VARIANT_KEY):
            raise SyncError(3, "reserved name {} cannot be used as variant name in data store".format(BrStores.DEF_VARIANT_KEY))

        newStorePaths = {'src': src, 'dest': dest, 'flags': flags}
        newVariant = {variant:newStorePaths}
        
        if (store in self.brstores):
            # store is there, see if this is a new variant
            if variant in self.brstores[store]:
                if (update == False): raise SyncError(3,"store [{}] variant [{}] already exists".format(store, variant))
            elif update is True:
                raise SyncError(3,"store [{}] variant [{}] does not exist, cannot update.".format(store, variant))

            updType = "Updating" if update else "Adding"
            
            message("{} new variant [{}] to store [{}]".format(updType, variant, store))                
            self.brstores[store][variant] = newStorePaths
        elif update is True:
                raise SyncError(3,"store [{}] does not exist, cannot update.".format(store))
        else:
            message("Adding new store [{}]".format(store))
            self.brstores[store] = newVariant

        message("Dumping the updated store dictionary to json disk file...")
        self._saveStores()
        
        return 0
        
    def renameStore(self,curStoreName,newStoreName):
        if( curStoreName in self.brstores ):
            if( newStoreName in self.brstores ):
                raise SyncError(15,"Store [{}] already exists.".format(newStoreName))
            self.brstores[newStoreName] = self.brstores.pop(curStoreName)
            
            self._saveStores()
            message("Store [{}] is now called [{}].".format(curStoreName,newStoreName))
            
            return 0
        
        raise SyncError(15,"Store [{}] doesn't exist.".format(curStoreName))
        
    def renameVariant(self,store,curVariant,newVariant):        
        if store in self.brstores:
            if curVariant in self.brstores[store]:
                if newVariant in self.brstores[store]:
                    raise SyncError(16,"Variant [{}] already exists in store [{}].".format(newVariant, store))

                if BrStores.DEF_VARIANT_KEY in self.brstores[store]:
                    if curVariant == self.brstores[store][BrStores.DEF_VARIANT_KEY]:
                        self.brstores[store][BrStores.DEF_VARIANT_KEY] = newVariant

                self.brstores[store][newVariant] = self.brstores[store].pop(curVariant)

                self._saveStores()
                message("Store Variant [{}] is now called [{}].".format(curVariant, newVariant))

                return 0

            raise SyncError(16,"Variant [{}] not found in store [{}]".format(curVariant, store))

        raise SyncError(16,"Store [{}] doesn't exist.".format(store))

    def removeStore(self,store):
        if( store in self.brstores ):
            self.brstores.pop(store)
            
            self._saveStores()
            message("Store [{}] has been removed.".format(store))
            
            return 0
        
        raise SyncError(17,"Store [{}] doesn't exist.".format(store))
        
    def removeVariant(self,store,variant):        
        if( store in self.brstores ):
            if( variant in self.brstores[store] ):
                if BrStores.DEF_VARIANT_KEY in self.brstores[store]:
                    if variant == self.brstores[store][BrStores.DEF_VARIANT_KEY]:
                        self.brstores[store].pop(BrStores.DEF_VARIANT_KEY)

                self.brstores[store].pop(variant)

                self._saveStores()
                message("Store Variant [{}] has been removed.".format(variant))

                return 0

            raise SyncError(18,"Variant [{}] not found in store [{}]".format(variant, store))

        raise SyncError(18,"Store [{}] doesn't exist.".format(store))

    def getDefault(self,store):
        if( store in self.brstores ):
            if (BrStores.DEF_VARIANT_KEY in self.brstores[store]):
                return self.brstores[store][BrStores.DEF_VARIANT_KEY]

            return None

        raise SyncError(20,"Store [{}] doesn't exist.".format(store))

    def setDefault(self,store,variant):        
        if( store in self.brstores ):
            if( variant in self.brstores[store] ):
                self.brstores[store][BrStores.DEF_VARIANT_KEY] = variant
                
                self._saveStores()
                message("Store Variant [{}] is now the default.".format(variant))
                
                return 0
                
            raise SyncError(20,"Variant [{}] not found in store [{}]".format(variant, store))
        
        raise SyncError(20,"Store [{}] doesn't exist.".format(store))
        
    def removeDefault(self, store):        
        if( store in self.brstores ):
            if(BrStores.DEF_VARIANT_KEY in self.brstores[store] ):
                self.brstores[store].pop(BrStores.DEF_VARIANT_KEY)
                
                self._saveStores()
                message("Store [{}] default has been removed.".format(store))
                
                return 0
                
            raise SyncError(21,"Store [{}] has no default variant".format(store))
        
        raise SyncError(21,"Store [{}] doesn't exist.".format(store))

    def dump_short_summary_header(self):
        message("{:>14}  {:<14}".format("Data store", "Variant Name"), False)
        message("{}".format('-'*40), False)

    def dump_short_summary(self, store):
        for variant in sorted(self.brstores[store]):
            if variant != BrStores.DEF_VARIANT_KEY:
                message("{:>14}: {:<14}".format(store, variant), False)

    def dump_long_summary_header(self):
        message("{:>14}  {:>14}  {}".format("Data store", "Variant Name", "<Src>, <Dest>, [Flags]"), False)
        message("{}".format('-'*79), False)

    def dump_long_summary(self, store):
        for variant in sorted(self.brstores[store]):
            if variant == BrStores.DEF_VARIANT_KEY:
                continue
            src = self.brstores[store][variant]['src']
            dest = self.brstores[store][variant]['dest']
            flags = self.brstores[store][variant]['flags']
            message("{:>14}: {:>14} <{}>, <{}>, [{}]".format(store, 
                                                             variant, 
                                                             src, 
                                                             dest, 
                                                             flags), False)

    def dump(self, short_summary, long_summary):
        from json import dumps
        if short_summary:
            self.dump_short_summary_header()
            for store in sorted(self._getStores()):
                self.dump_short_summary(store)
        elif long_summary:
            self.dump_long_summary_header()
            for store in sorted(self._getStores()):
                self.dump_long_summary(store)
        else:
            message(dumps(self.brstores,indent=4, sort_keys=True), False)
        return 0
        
    def dumpStore(self, store, short_summary, long_summary):
        from json import dumps
        if( store in self.brstores ):
            if short_summary:
                self.dump_short_summary_header()
                self.dump_short_summary(store)
            elif long_summary:
                self.dump_long_summary_header()
                self.dump_long_summary(store)
            else:
                message("{}\r\n{}\r\n".format(store, 
                                              dumps(self.brstores[store], indent=4, sort_keys=True)), False)
            return 0
            
        raise SyncError(31,"Store [{}] doesn't exist.".format(store))
        
    def initialize(self, jsonfile, makedefault):
        from os.path import isdir, isfile, split, join
        
        path,filename = split(jsonfile)
        if path and not isdir(path):
            raise SyncError(41, "Invalid path specified for JSON file [{}]".format(path))
        elif not path:
            jsonfile = join(me.whereami(),filename)

        if isfile(jsonfile):
            raise SyncError(42, "JSON file [{}] already exists.".format(jsonfile))

        stores = {
                    'storeName': {
                        'variantName':
                            {
                                'src': '~/Desktop/srcPath',
                                'dest': '~/Desktop/destPath',
                                'flags': ''
                            }
                    }
        }
        from json import dump
        with open(jsonfile, 'w') as fp:
            dump(stores, fp, indent=4)

        if makedefault:
            self.saveDefaultJSONStore(jsonfile)

        message("created new JSON data store file: [{}]".format(jsonfile))
        return 0


if __name__ == '__main__':
    message('brstores Library Module, not directly callable.', False)
    from sys import exit
    exit(1)
