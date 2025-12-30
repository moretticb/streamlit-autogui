import streamlit as st
import numpy as np
from PIL import Image

from autogui import autogui

st.set_page_config(layout="wide")

preview, pipeline = st.columns([0.7,0.3])

preview.subheader("Image")
tab_load, tab_proc, tab_orig = preview.tabs(["Upload", "Processed", "Original"])

def load_image() -> np.ndarray:
    """ {IO} """

    loaded_img = autogui("Image load testing tes", init_prompt="upload file")
    return loaded_img

with tab_load:
    img = load_image()


pipeline.subheader("Pipeline")


def proc_pipeline(img: np.ndarray) -> np.ndarray:
    """
    {IO}
    {VISUALIZATION}

Make sure to organize every step of the pipeline in an individual streamlit
expander. The image always must always go through every step of the pipeline
and return the final result.

Always add, for each expander, a component to toggle whether to apply that step
to the image. Never hide the components.

"""

    proc_img = autogui("Pipeline", history=autogui.STATIC, init_prompt="Brightness and contrast\n\nblack and white\n\ncrop")
    return proc_img

def view_img(img: np.ndarray) -> None:
    """ {IO} {VISUALIZATION} """

    autogui("img view", init_prompt="display image")
    return None




if isinstance(img,np.ndarray):
    proc = img.copy()

    with pipeline:
        proc = proc_pipeline(img=proc)

    proc = proc if isinstance(proc,type(img)) else img

    image = Image.fromarray(img)
    tab_orig.image(Image.fromarray(img), caption="Original", use_container_width=False)

    with tab_proc:
        view_img(proc)
