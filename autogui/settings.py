import re

from . import aiclient

s = None
GKEY = '_global'

class ddict(dict):
    def __getattr__(self, name):
        return self[name]
    
    def __setattr__(self, name, value):
        if isinstance(value, dict) and not isinstance(value, ddict):
            value = ddict(value)
        self[name] = value
    
    def __delattr__(self, name):
        del self[name]


def init(name, key, provider, model, patience, rerun, history, store_in, settings_key='autogui-settings'):
    actual_init = False
    if settings_key not in store_in:
        global s
        s = ddict({})
        store_in[settings_key] = s


    if "prefs" not in s:
        s.prefs = ddict({
            GKEY:ddict(instance="All")
            # keys related to local instances will fall here
        })

    key = key if key else re.sub("[^a-z0-9]","-",name.lower())
    if key not in s.prefs:
        actual_init = True
        s.prefs[key] = ddict(instance=name)


    if "providers" not in s:
        s.providers = aiclient.get_available()

    if actual_init: #not isset('provider',key):
        set_provider_model(provider, model, key)
        setpref("patience", patience, key)
        setpref("rerun", rerun, key)
        setpref("history", history, key) 

    return key, actual_init


def get_instance(key):
    return s.prefs[key]

def isset(setting, key=GKEY):
    return setting in s.prefs[key]

def _get(setting, key=GKEY):
    return s.prefs[key].get(setting, None)

def _set(setting, value, key=GKEY):
    s.prefs[key][setting] = value

def pop(setting, key=GKEY):
    if isset(setting, key=key):
        value = _get(setting, key=key)
        del s.prefs[key][setting]
        return value
    return None


def scope(setting,key=GKEY):
    # useful to track multiple settings that are dependent on one another
    return key if isset(setting,key) else GKEY

def getpref(setting=None, key=GKEY):
    if not setting:
        return s.prefs.get(key,None)
    return _get(setting, scope(setting,key))

def setpref(setting, value, key=GKEY, force_local=False):
    if value == None:
        if key!=GKEY:
            pop(setting, key)
        return
    
    key = GKEY if not isset(setting) else key
    if key==GKEY and not force_local:
        for key in s.prefs:
            if key==GKEY:
                _set(setting,value)
            elif isset(setting,key):
                #removes local setting, falling back to global
                pop(setting,key)
    elif force_local or value != _get(setting):
        _set(setting,value,key)
    else:
        pop(setting,key)


def get_provider_model(key=GKEY):
    provider = getpref('provider',key)
    sc = scope('provider', key)

    model = getpref('model',sc)

    return provider, model


def set_provider_model(provider, model, key=GKEY):
    if provider and model:
        key = GKEY if not isset('provider') else key
        if key==GKEY:
            for key in s.prefs:
                if key==GKEY:
                    _set('provider',provider)
                    _set('model',model)
                elif isset('provider',key):
                    #removes local setting, falling back to global
                    pop('provider',key)
                    pop('model',key)
        else:
            if provider == _get('provider') and model == _get('model'):
                #removes local setting, falling back to global
                pop('provider',key)
                pop('model',key)
            else:
                _set('provider',provider,key)
                _set('model',model,key)
    else:
        provider, model = aiclient.detect_default(s)
        set_provider_model(provider, model, key)


