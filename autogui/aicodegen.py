from openai import AzureOpenAI
import os
from . import schema, aiclient
import re
import hashlib

from importlib.metadata import packages_distributions

FUNCTION_NAME = "fcn"
FILE_NAME = "fcn.py"
SCHEMA = schema.FLOAT_IN_OUT

class InsufficientCapabilityError(Exception):
    def __init__(self, packages):
        message=f"Insufficient capabilities. Please install additional packages to enable this feature. Recommended are: {packages}."
        super().__init__(message)

IO = f"""

You are a coding assistant specialist in streamlit dashboards and have general
problem solving skills in python. Given a list of steps or features, your job
is to identify each step and then generate code to accomplish such tasks
sequentially. Provide UI elements for all parameters and/or inputs involved in
every step.

The code you generate will be included in function `{{FUNCTION_NAME}}`, which
takes `{{INPUT_SCHEMA}}` as input arguments and returns `{{OUTPUT_SCHEMA}}` as
output. Make sure to define unique keys for every streamlit component, but
never use any random function for it. Never use streamlit sidebar. Never use
any streamlit experimental feature. Never use caching.

Provide only code and nothing else. Never include markdown backticks. Prefer to
make use of the following packages: {{AVAILABLE_PKGS}}.

Never use streamlit titles or headers. If there are multiple steps, organize
those in expanders, tabs, or small subheaders. If there are few, or a single
task, do not enclose in any container, but simply render the due GUI elements.

Make sure to preserve the definition, input, and output of function
`{{FUNCTION_NAME}}`.

 """.replace("\n"," ")

VISUALIZATION = f"""

You are also a specialist in visualization. Make sure to use plots either when
explicitly requested, or only when necessary, to visualize some parameter
change, as a preview feature.

If images are associated to GUI components, make sure to organize in columns
(each group of preview and GUI in a set of columns), so any generated GUI is
relatable to the visualized result. Visualization on one side, GUI on the
other.

""".replace("\n"," ")

SYSTEM = f"{IO} {VISUALIZATION}"

def get_code(prompt, provider, model, system=SYSTEM, hist=None, compact_hist=False):
    # Templates first, containing variables
    system = system.format(
        IO=IO,
        VISUALIZATION=VISUALIZATION
    )

    # Then variables, which are possibly mentioned in templates
    system = system.format(
        FUNCTION_NAME=FUNCTION_NAME,
        INPUT_SCHEMA=schema.readable(SCHEMA[0]),
        OUTPUT_SCHEMA=schema.readable(SCHEMA[1]),
        AVAILABLE_PKGS=",".join(list(packages_distributions().keys()))
    )
    system = system.replace("\n"," ")

    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": prompt}
    ]

    if hist:
        hist.append({"role": "user", "content": prompt})
        messages = hist

        if compact_hist:
            # Saving tokens: keeping all system and user
            messages = [m for m in hist[:-2] if m["role"] in ["system","user"]]
            # and only the last assistant message, plus current message to send
            messages = messages + hist[-2:]

    response = aiclient.completions(provider, model, messages)

    hist = hist if hist else messages

    hist.append({
        "role": response.choices[0].message.role,
        "content": response.choices[0].message.content
    })

    return response.choices[0].message.content, hist


def update_code(code, file_name=FILE_NAME):
    with open(file_name, "w") as f:
        f.write(code)
    return None #hashlib.sha256(code.encode()).hexdigest()

def process_code(file_name=FILE_NAME, rerun=False):
    with open(file_name, "r") as f:
        code = f.read()

    hash_before = hashlib.sha256(remove_st_key_suffix(code).encode()).hexdigest()
    code = post_processing(code, rerun=rerun)
    hash_after = hashlib.sha256(remove_st_key_suffix(code).encode()).hexdigest()

    with open(file_name, "w") as f:
        f.write(code)

    return hash_before != hash_after

def generate_code(prompt, provider, model, system=SYSTEM, file_name=FILE_NAME, hist=None, compact_hist=False, rerun=False):
    new_code, hist = get_code(prompt, provider, model, system=SYSTEM, hist=hist, compact_hist=compact_hist)

    new_code = post_processing(new_code, rerun=rerun)

    digest = update_code(new_code, file_name=file_name)
    return hist, digest


def fix_code(error, provider, model, file_name=FILE_NAME, hist=None, compact_hist=False, rerun=False):
    with open(file_name) as f:
        code = f.read()
    code = preprocessing(code)
    prompt = (
        f"Fix: {error}."
        if hist and compact_hist else
        f"""The following piece of code:

```python
{code}
```

yields the following error:

```
{error}
```. Generate the new version of the code with no explanations and never include
markdown backticks. Only the code itself.
"""
    )

    hist, digest = generate_code(
        prompt,
        provider,
        model,
        system=SYSTEM,
        file_name=file_name,
        hist=hist,
        compact_hist=compact_hist,
        rerun=rerun
    )

    return hist, digest
    
def add_code(prompt, provider, model, file_name=FILE_NAME, hist=None, compact_hist=False, rerun=False):
    with open(file_name) as f:
        code = f.read()

    code = preprocessing(code)

    prompt = (
        f"Keep the code above and add the following features: {prompt}"
        if hist and compact_hist else
        f"""Keep the following piece of code:

```python
{code}
```

and add the following features:

```
{prompt}
```

Never modify the initial code, but simply merge it with the new features.
Generate the new version of the code with no explanations and never include
markdown backticks. Only the code itself. The new features must be appended as
the last tasks to be executed.

"""
        )
    hist, digest = generate_code(
        prompt,
        provider,
        model,
        system=SYSTEM,
        file_name=file_name,
        hist=hist,
        compact_hist=compact_hist,
        rerun=rerun
    )

    return hist, digest
    
def remove_code(prompt, provider, model, file_name=FILE_NAME, hist=None, compact_hist=False, rerun=False):
    with open(file_name) as f:
        code = f.read()
    
    code = preprocessing(code)

    prompt = (
        f"Remove the following features from the code above: {prompt}"
        if hist and compact_hist else
        f"""From the following piece of code:

```python
{code}
```

remove the following features:

```
{prompt}
```

Remove only what is referred to above. Never remove the other parts of the
code. Generate the new version of the code with no explanations and never
include markdown backticks. Only the code itself.

"""
    )
    hist, digest = generate_code(
        prompt,
        provider,
        model,
        system=SYSTEM,
        file_name=file_name,
        hist=hist,
        compact_hist=compact_hist,
        rerun=rerun
    )

    return hist, digest


def add_st_key_suffix(code, suffix="__k"):
    def gen_key_suffix(re_match):
        if suffix in re_match.group(2): # alternate pattern if suffix already there from past iteration
            new_id = re.sub(f'{suffix}[0-9]+',f'{suffix}{re_match.span()[1]}{re_match.span()[0]}',re_match.group(2))
            return f"{re_match.group(1)}{new_id}{re_match.group(3)}"

        return f"{re_match.group(1)}{re_match.group(2)}__k{re_match.span()[0]}{re_match.span()[1]}{re_match.group(3)}"

    return re.sub(r'(key=[\'"])([^"\']+)([\'"])', gen_key_suffix, code)

def remove_st_key_suffix(code, suffix="__k"):
    return re.sub(f"{suffix}[0-9]+", "", code)
    


def adapt_code_rerun(new_code, add=True):
    orig_form = f"def {FUNCTION_NAME}("
    proc_form = f"@st.fragment\ndef {FUNCTION_NAME}("

    if add and new_code.find(proc_form) < 0:
        new_code = new_code.replace(orig_form,proc_form)

    if not add:
        new_code = new_code.replace(proc_form,orig_form)

    return new_code

def post_processing(new_code, rerun):
    # removing annoying markdown backticks
    new_code = "\n".join(
        new_code.split("\n")[1:-1]
    ) if '```python' in new_code else new_code

    # making sure streamlit keys are unique
    new_code = add_st_key_suffix(new_code)

    # Adding code snippet for the rerun feature
    new_code = adapt_code_rerun(new_code, add=rerun)
        
    return new_code

def preprocessing(code):
    # removing rerun code if exists
    code = adapt_code_rerun(code, add=False)
    return code

