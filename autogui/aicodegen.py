from openai import AzureOpenAI
import os
from . import schema
import re

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

Make sure to preserve the definition, input, and output of functiion
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

client = AzureOpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),  
    api_version="2024-05-01-preview",
    azure_endpoint = os.getenv("OPENAI_API_BASE")
)


def is_generating():
    try:
        return len(get_code("hello world", system="You are a helpful assistant.")) > 0
    except:
        return False


def get_code(prompt, system=SYSTEM, model="gpt-4"):
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
    print("SYSTEM IS",system)

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt}
        ]
    )

    return response.choices[0].message.content


def update_code(code, file_name=FILE_NAME):
    with open(file_name, "w") as f:
        f.write(code)


def generate_code(prompt, system=SYSTEM, file_name=FILE_NAME):
    new_code = get_code(prompt, system=SYSTEM)

    # post processing
    new_code = add_st_key_suffix(new_code)

    update_code(new_code, file_name=file_name)
    return file_name


def fix_code(error, file_name=FILE_NAME):
    with open(file_name) as f:
        code = f.read()
    generate_code(
        f"""The following piece of code:

```python
{code}
```

yields the following error:

```
{error}
```. Generate the new version of the code with no explanations and never include
markdown backticks. Only the code itself.
""",
        system=SYSTEM,
        file_name=file_name
    )
    
def add_code(prompt, file_name=FILE_NAME):
    with open(file_name) as f:
        code = f.read()
    generate_code(
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

""",
        system=SYSTEM,
        file_name=file_name
    )
    
def remove_code(prompt, file_name=FILE_NAME):
    with open(file_name) as f:
        code = f.read()
    generate_code(
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

""",
        system=SYSTEM,
        file_name=file_name
    )


def add_st_key_suffix(code, suffix="__k"):
    def gen_key_suffix(re_match):
        if suffix in re_match.group(2): # alternate pattern if suffix already there from past iteration
            new_id = re.sub(f'{suffix}[0-9]+',f'{suffix}{re_match.span()[1]}{re_match.span()[0]}',re_match.group(2))
            return f"{re_match.group(1)}{new_id}{re_match.group(3)}"

        return f"{re_match.group(1)}{re_match.group(2)}__k{re_match.span()[0]}{re_match.span()[1]}{re_match.group(3)}"

    return re.sub(r'(key=[\'"])([^"\']+)([\'"])', gen_key_suffix, code)
    
