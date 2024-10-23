Set-Location "C:\Program Files\Netease\MuMu Player 12\shell"
./MuMuManager.exe control -v all restart
Start-Sleep -Seconds 60
Set-Location $PSScriptRoot
./run.ps1
