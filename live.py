import subprocess

import streamlit as st

p = subprocess.Popen(
    "adb -s localhost:5555 shell screenrecord --size 768x432 --output-format=h264 -",
    stdout=subprocess.PIPE,
    stderr=None,
    shell=True,
)
st.video(p.stdout)
