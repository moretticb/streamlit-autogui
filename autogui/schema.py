import inspect
import ast
from typing import get_type_hints


def from_parent_caller():
    # +------------------------------------------+
    # |                  STACK                   |
    # +-----+------------------------------------|
    # | idx |  function                          |
    # +-----+------------------------------------+
    # |  0  |  this very function                |
    # |  1  |  autogui (the streamlit component) |
    # |  2  |  function defined by user          |
    # +-----+------------------------------------+
    caller_frame = inspect.stack()[2]

    caller_function = caller_frame.function

    caller_module = inspect.getmodule(caller_frame[0])
    caller_func_obj = getattr(caller_module, caller_function)

    docstring = inspect.getsource(caller_func_obj).split('"""')
    if isinstance(docstring,list) and len(docstring) > 1 and 'def ' in docstring[0]:
        docstring = docstring[1]
    else:
        docstring = None

    args = caller_frame.frame.f_locals

    name, invars, outvars = from_func(caller_func_obj)
    return name, invars, outvars, docstring, args


def from_func(f):
    sig = inspect.signature(f)

    name = f.__name__
    args = {p.name:p.annotation for p in sig.parameters.values()}

    inferred_return_vars = []
    for node in ast.walk(ast.parse(inspect.getsource(f))):
        if isinstance(node, ast.Return):
            if isinstance(node.value, ast.Name):
                inferred_return_vars.append(node.value.id)
            elif isinstance(node.value, ast.Tuple):
                inferred_return_vars = inferred_return_vars + [v.id for v in node.value.elts]

    return_vars_types = sig.return_annotation
    return_vars_types = return_vars_types if isinstance(return_vars_types,tuple) else (return_vars_types,)
    out_vars = dict(zip(inferred_return_vars, return_vars_types))
    return name, args, out_vars

def from_vars(**kwargs):
    schema = dict()

    for var in kwargs:
        schema[var] = type(kwargs[var])

    return schema

def from_io(io):
    if isinstance(io, tuple):
        return (from_vars(io[0]), from_vars(io[1]))
    
    return (
        {v:io[v] for v in io if v.split("out_")[0]!=""},
        {v:io[v] for v in io if v.split("out_")[0]==""}
    )


def readable(schema):
    if isinstance(schema, tuple):
        return (readable(schema[0]), readable(schema[1]))

    txt = [
        f"{var}:{schema[var]}"
        for var in schema
    ]
    txt = ",".join(txt)
    return txt


FLOAT_IN_OUT = (from_vars(number=0.0), from_vars(out_number=0.0))
FLOAT_IN_BOOL_OUT = (from_vars(number=0.0), from_vars(out_number=False))
INT_IN_OUT = (from_vars(number=0), from_vars(out_number=0))
INT_IN_BOOL_OUT = (from_vars(number=0), from_vars(out_number=False))

