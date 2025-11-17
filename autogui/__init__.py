import os
import streamlit.components.v1 as components
import streamlit as st
from code_editor import code_editor
import time
from . import aicodegen
from . import schema
from pathlib import Path
import re

import tempfile
import sys
import importlib.util


_RELEASE=True

if not _RELEASE:
    _component_func = components.declare_component(
        "autogui",
        url="http://localhost:3001"
    )
else:
    parent_dir = os.path.dirname(os.path.abspath(__file__))
    build_dir = os.path.join(parent_dir, "frontend/build")
    _component_func = components.declare_component("autogui", path=build_dir)

HISTORY = 1<<0
FULL = 1<<1
COMPACT = 1<<2

def autogui(
    name,
    like=None,
    args=None,
    system=None,
    system_fix=None,
    features=None,
    patience=3,
    key=None,
    chat_flags = HISTORY + COMPACT,
    icon=":material/touch_app:"
):
    use_hist = (chat_flags & HISTORY) > 0
    compact_hist = (chat_flags & COMPACT) > 0

    @st.dialog(f"AutoGUI {name}", width="medium")
    def gen_tool(filename):
        tabs = [":material/code_blocks: Generate", ":material/build: Adjust"]
        if filename.exists():
            tabs = st.tabs(tabs)
            placeholder = "Describe features to generate, add, or remove. You can prompt for fixes."
        else:
            tabs = [st.container()]
            placeholder = "Describe features to generate..."

        with tabs[0]:
            prompt = st.text_area("",placeholder=placeholder)

            btns = st.columns(4 if len(tabs)>1 else 1)

            generate = btns[0].button("Generate", icon=":material/code_blocks:",key=f"{key}-gen", type="primary", use_container_width=True)
            add = False if len(btns)==1 else btns[1].button("Add", icon=":material/add:",key=f"{key}-add", type="secondary", use_container_width=True)
            remove = False if len(btns)==1 else btns[2].button("Remove", icon=":material/remove:",key=f"{key}-remove", type="secondary", use_container_width=True)
            fix = False if len(btns)==1 else btns[3].button("Fix", icon=":material/build:",key=f"{key}-fix", type="secondary", use_container_width=True)

            
            if generate:
                hist = aicodegen.generate_code(prompt, file_name=filename, compact_hist=compact_hist)
                st.session_state[hist_key] = hist if use_hist else None
                st.rerun()

            if add:
                hist = aicodegen.add_code(prompt, file_name=filename, hist=st.session_state[hist_key], compact_hist=compact_hist)
                st.session_state[hist_key] = hist
                st.rerun()

            if remove:
                hist = aicodegen.remove_code(prompt, file_name=filename, hist=st.session_state[hist_key], compact_hist=compact_hist)
                st.session_state[hist_key] = hist
                st.rerun()

            if fix:
                hist = aicodegen.fix_code(prompt, file_name=filename, hist=st.session_state[hist_key], compact_hist=compact_hist)
                st.session_state[hist_key] = hist
                st.rerun()

        if len(tabs) > 1: # if filename exists, and hence the ajust tab
            with tabs[1]:
                st.markdown("Generated code", help=f"at `{filename}`", unsafe_allow_html=True)
                with open(filename) as f:
                    resp = code_editor(f.read(), lang="python", options={"wrap":True, "showLineNumbers":True})

                st.markdown(":material/build: <sub>Press \u2318+Enter to apply changes.</sub>", unsafe_allow_html=True)

                if resp.get("type") == "submit":
                    aicodegen.update_code(resp["text"], file_name=filename)
                    st.rerun()

    if key == None:
        key=re.sub("[^a-z0-9]","-",name.lower())

    hist_key = f"{key}-hist"

    _ = _component_func(name=name, key=key)

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


    if st.button("", icon=icon, key=f"{key}-autogui-btn", use_container_width=True):
        gen_tool(filename)
    #prompt = st.text_area("prompt", key=f"{key}-prompt")
    gui_area = st.empty()
    error_area = st.empty()

    if filename.exists():
        p=0
        lacking_capabilities = []
        while p < patience:
            try:
                spec = importlib.util.spec_from_file_location(aicodegen.FUNCTION_NAME,str(filename))
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                with gui_area.container():
                    component_value = module.fcn(**args)
#                    error_area.empty()
                    break

            except Exception as e:
                if isinstance(e,ModuleNotFoundError):
                    lacking_capabilities.append(e.msg.split(' ')[-1])

                aicodegen.fix_code(str(e), file_name=filename, hist=st.session_state[hist_key], compact_hist=compact_hist)

                spec = importlib.util.spec_from_file_location(aicodegen.FUNCTION_NAME,str(filename))
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                p=p+1
#                st.write(p)
#                error_area.write(e)

        if len(lacking_capabilities) > 1:
            raise aicodegen.InsufficientCapabilityError(",".join(lacking_capabilities))
            

    #temp_dir.cleanup()
    return component_value

autogui.HISTORY = HISTORY
autogui.FULL = FULL
autogui.COMPACT = COMPACT
