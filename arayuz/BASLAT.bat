@echo off
rem Ay Inis Navigatoru arayuzunu yerel sunucuyla acar (internet gerekmez).
cd /d "%~dp0"
if not exist "veri\sites" (
  echo Veri paketi aciliyor: veri.zip ...
  powershell -NoProfile -Command "Expand-Archive -Path 'veri.zip' -DestinationPath '.' -Force"
)
start "" http://localhost:8767
python serve.py 8767
