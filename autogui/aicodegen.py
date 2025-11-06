from openai import AzureOpenAI
import os
from . import schema

FUNCTION_NAME = "fcn"
FILE_NAME = "fcn.py"
SCHEMA = schema.FLOAT_IN_OUT

SYSTEM = f"""

You are a coding assistant specialist in streamlit dashboards. Given a list of
steps, your job is to identify each step and then generate code to accomplish
such tasks sequentially. Provide UI elements for all parameters and/or inputs
involved in every step.

Provide only code and nothing else. Do not include markdown backticks.

The code you generate will be included in function `{{FUNCTION_NAME}}`, which
takes `{{INPUT_SCHEMA}}` as input arguments and returns
`{{OUTPUT_SCHEMA}}` as output. Make sure to define unique random keys
for every streamlit component. Never use streamlit sidebar. Never use any
streamlit experimental feature. Never use streamlit caching.

Each task must be individually detected and their UI and visualization elements
must be organized, separately, into their respective streamlit expander for
better user experience.

The IO of tasks must be chained as a pipeline. The output of one task must be
used as the input of the next, and the `{{OUTPUT_SCHEMA}}` is the final result
to be provided as output.

""".replace("\n"," ")

SYSTEM_FIX = f"""
You are a coding assistant specialist in streamlit and general problem solving
skills in python. Your job is to fix a given code snippet, given the error
message.

Never include markdown backticks (e.g., '```python```)', or any explanations or
text other than the new code itsewlf. Make sure to preserve the definition,
input, and output of function {{FUNCTION_NAME}}.
""".replace("\n"," ")

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
    system = system.format(
        FUNCTION_NAME=FUNCTION_NAME,
        INPUT_SCHEMA=schema.readable(SCHEMA[0]),
        OUTPUT_SCHEMA=schema.readable(SCHEMA[1])
    )
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
    update_code(get_code(prompt, system=SYSTEM), file_name=file_name)
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
        system=SYSTEM_FIX,
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
        system=SYSTEM_FIX,
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
        system=SYSTEM_FIX,
        file_name=file_name
    )
    
