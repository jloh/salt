'''
This module contains routines used to verify the matcher against the minions
expected to return
'''
# Import Python libs
import os
import glob
import fnmatch
import re

# Import Salt libs
import salt.payload


class CkMinions(object):
    '''
    Used to check what minions should respond from a target
    '''
    def __init__(self, opts):
        self.opts = opts
        self.serial = salt.payload.Serial(opts)

    def _check_glob_minions(self, expr):
        '''
        Return the minions found by looking via globs
        '''
        cwd = os.getcwd()
        os.chdir(os.path.join(self.opts['pki_dir'], 'minions'))
        ret = set(glob.glob(expr))
        os.chdir(cwd)
        return ret

    def _check_list_minions(self, expr):
        '''
        Return the minions found by looking via a list
        '''
        ret = []
        for fn_ in os.listdir(os.path.join(self.opts['pki_dir'], 'minions')):
            if fn_ in expr:
                if fn_ not in ret:
                    ret.append(fn_)
        return ret

    def _check_pcre_minions(self, expr):
        '''
        Return the minions found by looking via regular expressions
        '''
        ret = set()
        cwd = os.getcwd()
        os.chdir(os.path.join(self.opts['pki_dir'], 'minions'))
        reg = re.compile(expr)
        for fn_ in os.listdir('.'):
            if reg.match(fn_):
                ret.add(fn_)
        os.chdir(cwd)
        return ret

    def _check_grain_minions(self, expr):
        '''
        Return the minions found by looking via a list
        '''
        minions = set(os.listdir(os.path.join(self.opts['pki_dir'], 'minions')))
        if self.opts.get('minion_data_cache', False):
            cdir = os.path.join(self.opts['cachedir'], 'minions')
            if not os.path.isdir(cdir):
                return list(minions)
            for id_ in os.listdir(cdir):
                if not id_ in minions:
                    continue
                datap = os.path.join(cdir, id_, 'data.p')
                if not os.path.isfile(datap):
                    continue
                grains = self.serial.load(open(datap)).get('grains')
                comps = expr.split(':')
                if len(comps) < 2:
                    continue
                if comps[0] not in grains:
                    minions.remove(id_)
                    continue
                if isinstance(grains.get(comps[0]), list):
                    # We are matching a single component to a single list member
                    found = False
                    for member in grains[comps[0]]:
                        if fnmatch.fnmatch(str(member).lower(), comps[1].lower()):
                            found = True
                            break
                    if found:
                        continue
                    minions.remove(id_)
                    continue
                if fnmatch.fnmatch(
                    str(grains.get(comps[0], '').lower()),
                    comps[1].lower(),
                    ):
                    continue
                else:
                    minions.remove(id_)
        return list(minions)

    def _check_grain_pcre_minions(self, expr):
        '''
        Return the minions found by looking via a list
        '''
        minions = set(os.listdir(os.path.join(self.opts['pki_dir'], 'minions')))
        if self.opts.get('minion_data_cache', False):
            cdir = os.path.join(self.opts['cachedir'], 'minions')
            if not os.path.isdir(cdir):
                return list(minions)
            for id_ in os.listdir(cdir):
                if not id_ in minions:
                    continue
                datap = os.path.join(cdir, id_, 'data.p')
                if not os.path.isfile(datap):
                    continue
                grains = self.serial.load(open(datap)).get('grains')
                comps = expr.split(':')
                if len(comps) < 2:
                    continue
                if comps[0] not in grains:
                    minions.remove(id_)
                if isinstance(grains[comps[0]], list):
                    # We are matching a single component to a single list member
                    found = False
                    for member in grains[comps[0]]:
                        if re.match(comps[1].lower(), str(member).lower()):
                            found = True
                    if found:
                        continue
                    minions.remove(id_)
                    continue
                if re.match(
                    comps[1].lower(),
                    str(grains[comps[0]]).lower()
                    ):
                    continue
                else:
                    minions.remove(id_)
        return list(minions)

    def _all_minions(self, expr=None):
        '''
        Return a list of all minions that have auth'd
        '''
        return os.listdir(os.path.join(self.opts['pki_dir'], 'minions'))

    def check_minions(self, expr, expr_form='glob'):
        '''
        Check the passed regex against the available minions' public keys
        stored for authentication. This should return a set of ids which
        match the regex, this will then be used to parse the returns to
        make sure everyone has checked back in.
        '''
        try:
            minions = {'glob': self._check_glob_minions,
                       'pcre': self._check_pcre_minions,
                       'list': self._check_list_minions,
                       'grain': self._check_grain_minions,
                       'grain_pcre': self._check_grain_pcre_minions,
                       'exsel': self._all_minions,
                       'pillar': self._all_minions,
                       'compound': self._all_minions,
                      }[expr_form](expr)
        except Exception:
            minions = expr
        return minions

