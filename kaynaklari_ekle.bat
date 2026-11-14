@echo off
setlocal
rem Nasa_Space_Mokap'taki kaynak dosyalari Final V1.0'a kopyalar (yalniz okur, Mokap'a dokunmaz).
rem robocopy dosyalarin orijinal tarihlerini korur.
set "M=C:\Users\Ege\Desktop\Nasa_Space_Mokap"
set "F=%~dp0"
if "%F:~-1%"=="\" set "F=%F:~0,-1%"
if not exist "%M%\ay-inis-navigatoru\data\raw\LDEM_80S_80MPP_ADJ.TIF" (
  echo Nasa_Space_Mokap bulunamadi: %M%
  pause
  exit /b 1
)
if not exist "%F%\arayuz\build.py" (
  echo Bu dosya Final V1.0 klasorunun icinde calistirilmali.
  pause
  exit /b 1
)
set "R=/R:1 /W:1 /NP /NFL /NDL /DCOPY:T"
echo.
echo 1/4 NASA ham verileri -^> data\raw
robocopy "%M%\ay-inis-navigatoru\data\raw" "%F%\data\raw" LDEM_80S_80MPP_ADJ.TIF %R%
robocopy "%M%\ay-inis-navigatoru\data\raw\pgda" "%F%\data\raw\pgda" /E %R%
robocopy "%M%\ay-inis-navigatoru\data\raw\kernels" "%F%\data\raw\kernels" de421.bsp pck00008.tpc %R%
robocopy "%M%\ay-inis-navigatoru\data\raw\usgs_regions" "%F%\data\raw\usgs_bolgeler" /E %R%
echo.
echo 2/4 Onceki hesap projesi (kod, belgeler, 20 m arazi parcalari) -^> kaynak\ay-inis-navigatoru
robocopy "%M%\ay-inis-navigatoru" "%F%\kaynak\ay-inis-navigatoru" /E /XD .git .venv __pycache__ .pytest_cache lunar_nav.egg-info "%M%\ay-inis-navigatoru\data\raw" %R%
echo.
echo 3/4 Onceki arayuz projesi (notlar, eski veri seti, Blender, dogrulama goruntuleri) -^> kaynak\tasarim
robocopy "%M%\tasarim" "%F%\kaynak\tasarim" /E /XD .git prototip_yedek_1311 prototip_yedek_1311b "%M%\tasarim\prototip\vendor" "%M%\tasarim\prototip\yayin" /XF malapert_acilis.mp4 index.html baslat.bat %R%
echo.
echo 4/4 Kontrol
set OK=1
for %%f in ("data\raw\LDEM_80S_80MPP_ADJ.TIF" "data\raw\pgda\AVGVISIB_75S_120M_201608.TIF" "data\raw\pgda\AVGVISIB_75S_120M_201608_EARTH.TIF" "data\raw\usgs_bolgeler\A3_9regions-lonlat-simplified.geojson" "kaynak\ay-inis-navigatoru\src\lunar_nav\horizon.py" "kaynak\tasarim\veri\sites.json" "kaynak\tasarim\blender\malapert_render.py") do (
  if not exist "%F%\%%~f" ( echo   EKSIK: %%~f & set OK=0 )
)
if "%OK%"=="1" ( echo   Butun kaynak dosyalar yerinde. ) else ( echo   Bazi dosyalar kopyalanamadi, yukaridaki satirlara bakin. )
echo.
pause
