import os
import json

from importlib.metadata import packages_distributions

import aisuite as ai

import importlib

client = ai.Client()

try:
    azure_client = getattr(importlib.import_module("openai"),"AzureOpenAI")(
        api_key=os.getenv("AZURE_API_KEY"),
        api_version=os.getenv("AZURE_API_VERSION"),
        azure_endpoint = os.getenv("AZURE_API_BASE")
    )
except:
    azure_client = None

def get_client(provider):
    return azure_client if provider.lower() == 'azure' else client


def completions(provider, model, messages):
    client = get_client(provider)

    # Azure is the exception, as it is not currently working with aisuite
    model=model if provider == 'azure' else f"{provider}:{model}"

    return client.chat.completions.create(model=model, messages=messages)

def get_available():
    # returns a dict:
    # - key: the name of the provider package that must be installed
    # - value: availability of that particular provider:
    #   - installed: whether package of that provider is installed
    #   - missing: env vars still to be set
    #   - env: all mandatory envs that must be set
    #   - default: model to be used by default, if any


    # requirements to validate:
    # - key: provider python packages to install
    # - value: mandatory env vars and default model if any

    module_dir = os.path.dirname(__file__)
    with open(os.path.join(module_dir, "providers.json"), "r") as f:
        providers = json.load(f)

    pkgs = packages_distributions()
    ready = {}
    not_ready = {}
    for provider in providers:
        p = providers[provider]

        if provider=='azure': # special case
            p['installed'] = azure_client != None
        else:
            p["installed"] = provider in pkgs

        p["missing"] = [v for v in p["env"] if v not in os.environ]

        warnings = []
        triage = ready

        if not p["installed"]:
            triage=not_ready
            warnings.append("Module not installed")

        if len(p["missing"]) > 0:
            triage=not_ready
            for env in p["missing"]:
                warnings.append(f"`{env}` is not set")
        
        p["warnings"] = warnings

        triage[provider] = p
                
    #return providers
    return dict(**ready, **not_ready)


def detect_default(s=None):
    providers = s.providers if s else get_available()
    for p in providers:
        if len(providers[p]['warnings']) == 0 and "default" in providers[p]:
            return p, providers[p]['default']

    return None, None
