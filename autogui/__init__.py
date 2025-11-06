import os
import streamlit.components.v1 as components
import streamlit as st
from code_editor import code_editor
import time
from . import aicodegen
from . import schema
from pathlib import Path

import tempfile
import sys
import importlib.util


@st.dialog("AutoGUI settings", width="medium")
def gen_tool(key, filename):

    tab_gen, tab_adj = st.tabs([":material/code_blocks: Generate", ":material/build: Adjust"])

    with tab_gen:
        prompt = st.text_area("")

        gen_col, add_col, rem_col = st.columns(3)
        generate = gen_col.button("Generate", icon=":material/code_blocks:",key=f"{key}-gen", type="primary", use_container_width=True)
        add = add_col.button("Add", icon=":material/add:",key=f"{key}-add", type="secondary", use_container_width=True)
        remove = rem_col.button("Remove", icon=":material/remove:",key=f"{key}-remove", type="secondary", use_container_width=True)

        if generate:
            aicodegen.generate_code(prompt, file_name=filename)
            st.rerun()

        if add:
            aicodegen.add_code(prompt, file_name=filename)
            st.rerun()

        if remove:
            aicodegen.remove_code(prompt, file_name=filename)
            st.rerun()

    with tab_adj:
        if not filename.exists():
            st.write("No generated code. Use Generate tab to add features, and then this tab for fine adjustments.")
        else:
            st.markdown(f"<sub>{filename}</sub>", unsafe_allow_html=True)
            with open(filename) as f:
                resp = code_editor(f.read(), lang="python", options={"wrap":True, "showLineNumbers":True})

            st.markdown(":material/build: <sub>Press Command+Enter to apply changes.</sub>", unsafe_allow_html=True)

            if resp.get("type") == "submit":
                aicodegen.update_code(resp["text"], file_name=filename)
                st.rerun()
                
            

def autogui(
    name,
    like=None,
    args=None,
    system=None,
    system_fix=None,
    features=None,
    patience=3,
    key=None,
):

    if not aicodegen.is_generating():
        raise Exception("Provide OpenAI credentials")

    if key == None:
        key=name

    if like==None or args==None:
        name, invars, outvars, system, args = schema.from_parent_caller()
    else:
        name, invars, outvars = schema.from_func(like)

    component_value = None
    if len(outvars) > 1:
        component_value = (None for _ in outvars)

    #aicodegen.FUNCTION_NAME = name
    if system:
        aicodegen.SYSTEM = system
    if system_fix:
        aicodegen.SYSTEM_FIX = system_fix

    aicodegen.SCHEMA = (invars,outvars)

    file_key = f"{key}-aicode"
    if file_key not in st.session_state:
        st.session_state[file_key] = tempfile.TemporaryDirectory(delete=False)

    filename = Path(st.session_state[file_key].name) / aicodegen.FILE_NAME
    sys.path.insert(0, filename.parent)
    #module = str(filename.parent / filename.stem)
    module = str(filename.stem)

    #generate = st.button("", icon=":material/code_blocks:",key=f"{key}-gen", type="primary")

    if st.button("", icon=":material/touch_app:",key=f"{key}-a", use_container_width=True):
        gen_tool(key, filename)
    #prompt = st.text_area("prompt", key=f"{key}-prompt")
    gui_area = st.container()
    error_area = st.empty()

    if filename.exists():
        p=0
        while p < patience:
            try:
                spec = importlib.util.spec_from_file_location(aicodegen.FUNCTION_NAME,str(filename))
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                with gui_area:
                    component_value = module.fcn(**args)
                    error_area.empty()
                    break

            except Exception as e:
                aicodegen.fix_code(str(e), file_name=filename)

                spec = importlib.util.spec_from_file_location(aicodegen.FUNCTION_NAME,str(filename))
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                p=p+1
                st.write(p)
                error_area.write(e)
            

    #temp_dir.cleanup()
    return component_value
