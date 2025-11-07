import streamlit as st

from autogui import autogui

num = st.number_input("some input",0)

#def pipeline(n: int) -> int:
#    return True
#
#value_a = autogui("teste", like=pipeline, args=dict(n=num))
#st.write(value_a)

def pipeline(n: int) -> (float,bool):
    """
You are a coding assistant specialist in streamlit dashboards. Given a list of
steps, your job is to identify each step and then generate code to accomplish
such tasks sequentially. Provide UI elements for all parameters and/or inputs
involved in every step.

Provide only code and nothing else. Do not include markdown backticks.

The code you generate will be included in function `{FUNCTION_NAME}`, which
takes `{INPUT_SCHEMA}` as input arguments and returns `{OUTPUT_SCHEMA}` as
output. One output is the result itself, the other is whether the output is
prime (no GUI for the latter). Make sure to define unique random keys for every
streamlit component. Never use streamlit sidebar. Never use any streamlit
experimental feature. Never use streamlit caching.

Each task must be individually detected and their UI and visualization elements
must be organized, separately, into their respective streamlit expander for
better user experience.

The IO of tasks must be chained as a pipeline. The output of one task must be
used as the input of the next, and the `{OUTPUT_SCHEMA}` is the final result
to be provided as output.
    """
    val1, val2 = autogui("teste")
    return val1,val2

value, prime = pipeline(n=num)


st.write(f"Output is {value}")
if prime:
    st.write(f"and {value} is prime")



def pipeline2(n: int) -> (float,bool):
    """
You are a coding assistant specialist in streamlit dashboards. Given a list of
steps, your job is to identify each step and then generate code to accomplish
such tasks sequentially. Provide UI elements for all parameters and/or inputs
involved in every step.

Provide only code and nothing else. Do not include markdown backticks.

The code you generate will be included in function `{FUNCTION_NAME}`, which
takes `{INPUT_SCHEMA}` as input arguments and returns `{OUTPUT_SCHEMA}` as
output. One output is the result itself, the other is whether the output is
prime (no GUI for the latter). Make sure to define unique random keys for every
streamlit component. Never use streamlit sidebar. Never use any streamlit
experimental feature. Never use streamlit caching.

Each task must be individually detected and their UI and visualization elements
must be organized, separately, into their respective streamlit expander for
better user experience.

The IO of tasks must be chained as a pipeline. The output of one task must be
used as the input of the next, and the `{OUTPUT_SCHEMA}` is the final result
to be provided as output.
    """
    val1, val2 = autogui("teste2")
    return val1,val2

value, prime = pipeline2(n=num)

st.write(f"Output is {value}")
if prime:
    st.write(f"and {value} is prime")

