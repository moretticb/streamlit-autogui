import streamlit as st
import numpy as np

import matplotlib
import matplotlib.pyplot as plt
plt.style.use('dark_background')

from mpl_toolkits.axes_grid1 import make_axes_locatable

from scipy.io import wavfile

from pathlib import Path
from io import BytesIO

from autogui import autogui

sample_rate = 22050  # Example sample rate

def process_audio(waveform:np.ndarray, sample_rate:int) -> np.ndarray:
    """
    {IO}{VISUALIZATION} You are also a specialist in signal processing for audio that
generates code solutions for series of techniques to process audio. Provide visualization for any technique or parameters deemed necessary. Never plot any audio waveform or spectrogram.
    """

    filtered = autogui("Audio processing", init_prompt="noise reduction by amplitude threshold filter\nbandpass filter set to human speech range", model="MODEL_NAME", provider="PROVIDER_NAME")

    return filtered




def load_audio(audio):
    sample_rate, waveform = wavfile.read(audio)
    if len(waveform.shape) > 1:
        waveform = np.mean(waveform, axis=1)

    return sample_rate, waveform


def write_audio(sample_rate, waveform):
    buffer = BytesIO()
    wavfile.write(buffer, sample_rate, waveform.astype(np.int16))
    return buffer

from scipy.signal import stft

def spectrogram_fig(audio, samplerate, segment_size=1024, overlap=512, db=None, db_scale=True, log_scale=False, y_axis_position='left', ax=None, fig=None):
    f, t, Zxx = stft(audio, fs=samplerate, window='hann', nperseg=segment_size, noverlap=overlap)
    spectrogram = 20 * np.log10(np.abs(Zxx) + 1e-6)

    if log_scale:
        f = np.logspace(np.log10(f[1]), np.log10(f[-1]), len(f))

    if ax is None and fig is None:
        fig, ax = plt.subplots(2, figsize=(13, 9), gridspec_kw={'height_ratios': [4, 1]}, sharex=True)

    im = ax[0].imshow(spectrogram, aspect='auto', origin='lower', extent=[t[0], t[-1], f[0], f[-1]])

    if log_scale:
        ax[0].set_yscale('log')
        ax[0].yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{x:.0f}'))
        ax[0].grid(which='both', linestyle='-', linewidth=0.5)

    if db_scale:
        if db:
            im.set_clim(db[0], db[1])
        divider = make_axes_locatable(ax[0])
        cax = divider.append_axes('bottom', size='6%', pad=0.6)
        fig.colorbar(im, cax=cax, location="bottom").set_label("Magnitude (dB)")

    ax[0].set_xlabel('Time (s)')
    ax[0].set_ylabel('Frequency (Hz)' if y_axis_position == 'left' else '')
    if y_axis_position == 'right':
        ax[0].yaxis.tick_right()
        ax[0].yaxis.set_label_position("right")

    fig.tight_layout()
    return fig, ax, (np.min(spectrogram), np.max(spectrogram))

def waveform_fig(waveform, sample_rate, fig=None, ax=None):
    if ax is None and fig is None:
        fig, ax = plt.subplots(figsize=(13, 2))
    fig.tight_layout()

    time = np.linspace(
        0.0,
        len(waveform)/sample_rate, # duration in seconds
        len(waveform)
    )

    ax.plot(time,waveform)
    if fig.axes[0].yaxis.get_ticks_position() == 'right':
        ax.yaxis.tick_right()
    _ = [ax.spines[side].set_visible(False) for side in ['top', 'right', 'left', 'bottom']]

    fig.axes[0].xaxis.label.set_visible(False)
    ax.set_xlabel("Time")
    #ax.set_ylabel("Amplitude")

    return fig, ax, (waveform.min(), waveform.max())


import matplotlib.colorbar as cbar
import matplotlib.colors as mcolors

def db_scale(scale_range, figsize=(23,1)):
    fig, ax = plt.subplots(figsize=figsize)
    fig.subplots_adjust(bottom=0.5)
    fig.tight_layout()

    cmap = plt.cm.viridis
    norm = mcolors.Normalize(vmin=scale_range[0], vmax=scale_range[1])

    bar = cbar.ColorbarBase(ax, cmap=cmap, norm=norm, orientation='horizontal')

    bar.ax.xaxis.set_ticks_position('top')
    bar.ax.xaxis.set_label_position('top')
    bar.ax.tick_params(axis='x', labelsize=10, pad=-20, direction='in', colors='white')

    bar.ax.text(np.mean(scale_range), 0.5, "Magnitude (dB)", ha="center", va="center", color="white")

    return fig, ax


st.set_page_config(layout="wide")

if "pipeline_prompt" not in st.session_state:
    st.session_state["pipeline_prompt"] = ""

if "counter" not in st.session_state:
    st.session_state["counter"] = 0

db_scale_area = st.empty()

before_after = st.container()
before, after = before_after.columns([0.5,0.5], border=False, gap="small")

before = before.container(border=False)
before_fig = before.empty()
input_mode, audio_area = before.columns([0.1,0.9])
rec = input_mode.toggle(":material/mic:", value=True, disabled=True)
audio_area = audio_area.empty()
input_params = before.expander("Input and visualization")
log_scale = input_params.toggle("Logarithmic scale")


after = after.container(border=False)
after_fig = after.empty()
fx, fx_audio_area = after.columns([0.1,0.9])
use_fx = fx.toggle(":material/function:", disabled=True)
fx_audio_area = fx_audio_area.empty()
filter_params = after.empty()

dummy_fig,_ = plt.subplots(figsize=(13,9))
before_fig.pyplot(dummy_fig, transparent=True)
after_fig.pyplot(dummy_fig, transparent=True)


with before:
    if rec:
        audio = audio_area.audio_input("talk", label_visibility="collapsed")

if audio:
    sample_rate, waveform = load_audio(audio)

    fig_before, ax_before, scale_rng_before = spectrogram_fig(waveform, sample_rate, log_scale=log_scale, db_scale=not use_fx)
    _,_,wave_amp = waveform_fig(waveform, sample_rate, fig=fig_before, ax=ax_before[1])

    if use_fx:
        with after:
            filtered = process_audio(waveform, sample_rate)

        if not isinstance(filtered, np.ndarray):
            filtered = waveform
        
        filtered_audio = write_audio(sample_rate, filtered)


        audio = filtered_audio
        fx_audio_area.audio(filtered_audio)

        fig_after, ax_after, scale_rng_after = spectrogram_fig(filtered if use_fx else waveform, sample_rate, log_scale=log_scale, db_scale=not use_fx, y_axis_position="right")
        _,ax,_ = waveform_fig(filtered, sample_rate, fig=fig_after, ax=ax_after[1])
        ax.set_ylim(wave_amp[0],wave_amp[1])

        final_scale_rng = (np.min([scale_rng_before[0],scale_rng_after[0]]), np.max([scale_rng_before[1],scale_rng_after[1]]))
        scale_fig,_ = db_scale(final_scale_rng)
        db_scale_area.pyplot(scale_fig, transparent=True)

        if isinstance(ax_before[0].get_children()[0], matplotlib.image.AxesImage):
            ax_before[0].get_children()[0].set_clim(final_scale_rng)
        else:
            st.write(ax_before[0].get_children())
        ax_before[0].set_title("Raw")
        before_fig.pyplot(fig_before, transparent=True)

        ax_after[0].get_children()[0].set_clim(final_scale_rng)
        ax_after[0].set_title("Processed")
        after_fig.pyplot(fig_after, transparent=True)

