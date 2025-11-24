import os
import streamlit.components.v1 as components
import streamlit as st
from code_editor import code_editor
import time
from . import aiclient
from . import aicodegen
from . import schema
from . import settings as s
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

STATIC = 0 #1<<0
COMPACT = 1 #1<<2
FULL = 2 #1<<1

def autogui(
    name,
    init_prompt=None,
    provider=None,
    model=None,
    patience=3,
    rerun=True,
    history = COMPACT,
    like=None,
    args=None,
    system=None,
    system_fix=None,
    features=None,
    key=None,
    icon=":material/touch_app:"
):
    use_hist = history == STATIC
    compact_hist = history == COMPACT

    @st.dialog(f"AutoGUI {name}", width="medium")
    def gen_tool(filename):
        tabnames = [":material/code_blocks: Generate", ":material/build: Adjust", ":material/settings: Settings"]

        if filename.exists():
            placeholder = "Describe features to generate, add, or remove. You can prompt for fixes."
        else:
            tabnames = [t for t in tabnames if "Adjust" not in t]
            placeholder = "Describe features to generate..."

        tabs = st.tabs(tabnames)
        def tab(tabname, label=False):
            return next((tabnames[i] if label else tabs[i] for i,t in enumerate(tabnames) if tabname.lower() in t.lower()),None)

        with tab("generate"):
            try:
                current_model = f"Prompt ({": ".join(s.get_provider_model(key))})"
            except:
                current_model = f":material/error: Unable to find a valid model. Please provide a valid model in **{tab('settings', label=True)}**."
            prompt = st.text_area(current_model,placeholder=placeholder)

            btns = st.columns(4 if tab("adjust") else 1)

            cmd = {
                "generate" : btns[0].button("Generate", icon=":material/code_blocks:",key=f"{key}-gen", type="primary", use_container_width=True),
                "add" : False if not tab("adjust") else btns[1].button("Add", icon=":material/add:",key=f"{key}-add", type="secondary", use_container_width=True),
                "remove" : False if not tab("adjust") else btns[2].button("Remove", icon=":material/remove:",key=f"{key}-remove", type="secondary", use_container_width=True),
                "fix" : False if not tab("adjust") else btns[3].button("Fix", icon=":material/build:",key=f"{key}-fix", type="secondary", use_container_width=True)
            }

            for c in cmd:
                if cmd[c]:
                    provider,model = s.get_provider_model(key)

                    if c=='generate':
                        hist, digest = aicodegen.generate_code(prompt, provider, model, file_name=filename, compact_hist=compact_hist)
                        st.session_state[hist_key] = hist if use_hist else None
                    else:
                        hist, digest = getattr(aicodegen,f"{c}_code")(prompt, provider, model, file_name=filename, hist=st.session_state[hist_key], compact_hist=compact_hist)
                        st.session_state[hist_key] = hist

                    st.rerun()
                    break
            


        if tab("adjust"):
            with tab("adjust"):
                st.markdown("Generated code", help=f"at `{filename}`", unsafe_allow_html=True)
                with open(filename) as f:
                    resp = code_editor(f.read(), lang="python", options={"wrap":True, "showLineNumbers":True})

                st.markdown(":material/build: <sub>Press \u2318+Enter to apply changes.</sub>", unsafe_allow_html=True)

                if resp.get("type") == "submit":
                    aicodegen.update_code(resp["text"], file_name=filename)
                    st.rerun()

        with tab("settings"):
            st.header("AI")
            c1,c2 = st.columns(2)
            try:
                def_provider, _ = s.get_provider_model(key)
            except:
                def_provider = None
            provider = c1.selectbox("Provider",[p for p in s.s.providers], index=0 if not def_provider else list(s.s.providers).index(def_provider))
            if provider:
                disabled = len(s.s.providers[provider]["warnings"])>0
                err = "\n\n:material/error: "
                err = err+err.join(s.s.providers[provider]["warnings"]) if disabled else ""
                st.markdown(err, unsafe_allow_html=True)
                deployment_name = c2.text_input("Model",value=s.s.providers[provider].get("default",""), disabled=disabled, help=s.s.providers[provider].get('help',''))


            c1,c2,c3 = st.columns(3)
            patience = c1.number_input("Patience", value=s.getpref("patience",key), min_value=1, max_value=100)

            hist_opt = ["Static","Compact","Full"]
            hist=c3.selectbox("Prompt history", hist_opt, index=s.getpref("history",key), help="Format of chat history. Choose `Static` for one-time or few requests, `Compact` for multiple chained requests (e.g., generate, then add/remove/fix multiple times), or `Full` to preserve the whole verbosy history. Notice that the longer the history, the more expensive it is (cost and time wise).")
            hist=hist_opt.index(hist)


            st.header("Streamlit")
            rerun = st.toggle("Refresh upon GUI change", value=s.getpref("rerun",key), help="This adds an extra button")

            st.header("Scope")
            apply_to = s.GKEY if st.toggle("For all AutoGUI instances", value=True) else key

            c1,c2 = st.columns([0.2,0.8], vertical_alignment="center")
            if c1.button("Apply",key="autogui_apply_settings", use_container_width=True, disabled=disabled):
                do_apply = True
                
                if not deployment_name:
                    details = "" if "help" not in s.s.providers[provider] else f"Refer to {s.s.providers[provider]['help']} for more details."
                    c2.write(f"Model name not provided. {details}")

                if do_apply:
                    s.set_provider_model(provider, deployment_name, apply_to)
                    s.setpref("patience",patience,apply_to)
                    s.setpref("rerun",rerun,apply_to)
                    s.setpref("history",hist,apply_to)
                    c2.write(f"Settings applied to **{s.getpref(key=apply_to).instance}**.")



    # applying initial global settings
    key=s.init(name, key, provider, model, patience, rerun, history, st.session_state)
    st.write(s.s.prefs)
    hist_key = f"autogui-{key}-hist"

    settings_key = 'autogui-settings'

    digest=None
    #hashkey = f"autogui-{key}-digest"

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

    file_key = f"autogui-{key}-code"
    if file_key not in st.session_state:
        st.session_state[file_key] = tempfile.TemporaryDirectory(delete=False)

    filename = Path(st.session_state[file_key].name) / aicodegen.FILE_NAME
    sys.path.insert(0, filename.parent)
    #module = str(filename.parent / filename.stem)
    module = str(filename.stem)

    display_icon = icon
    if not filename.exists() and init_prompt:
        try:
            provider,model = s.get_provider_model(key)
            hist, digest = aicodegen.generate_code(init_prompt, provider, model, file_name=filename, compact_hist=compact_hist)
            st.session_state[hist_key] = hist if use_hist else None
        except Exception as e:
            st.write(e)
            display_icon = ":material/error:"

    @st.fragment
    def open_dialog():
        if st.button("", icon=display_icon, key=f"{key}-autogui-btn", use_container_width=True):
            gen_tool(filename)

    open_dialog()

    _ = _component_func(name=name, key=key)

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

                #st.session_state[hashkey] = digest
                with gui_area.container():
                    component_value = module.fcn(**args)
                    # TODO: render button if enabled in settings, together with fragment post processing
                    #if st.button("apply all",key=f"autogui-{key}-frag-apply"):
                    #    pass
#                    error_area.empty()
                break

            except Exception as e:
                if isinstance(e,ModuleNotFoundError):
                    lacking_capabilities.append(e.msg.split(' ')[-1])

                provider,model =  s.get_provider_model()
                aicodegen.fix_code(str(e), provider, model, file_name=filename, hist=st.session_state[hist_key], compact_hist=compact_hist)

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

autogui.STATIC = STATIC
autogui.FULL = FULL
autogui.COMPACT = COMPACT
