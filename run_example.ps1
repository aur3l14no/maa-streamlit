$MyInvocation.MyCommand.Path | Split-Path | Push-Location
adb kill-server
adb start-server
.venv/Scripts/activate.ps1
streamlit run Dashboard.py