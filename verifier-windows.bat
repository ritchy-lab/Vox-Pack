@echo off
chcp 65001 >nul
setlocal EnableExtensions
cd /d "%~dp0"
title Vox-Pack 2 - verification Windows

echo ============================================================
echo  Vox-Pack 2 - verification sur Windows
echo ============================================================
echo.

rem ---- 1. Python -------------------------------------------------
set "PY="
py -3.11 -c "import sys" >nul 2>nul && set "PY=py -3.11"
if not defined PY (
    py -3 -c "import sys" >nul 2>nul && set "PY=py -3"
)
if not defined PY (
    python -c "import sys" >nul 2>nul && set "PY=python"
)
if not defined PY (
    echo Python 3 est introuvable.
    echo Installez-le depuis python.org en cochant "Add python.exe to PATH",
    echo puis relancez ce fichier.
    pause
    exit /b 1
)
echo Python : %PY%
echo.

rem ---- 2. Environnement ------------------------------------------
if exist "venv\pyvenv.cfg" if not exist "venv\Scripts\python.exe" (
    echo Un environnement venu d'un autre systeme est present dans venv\.
    echo Supprimez le dossier venv, puis relancez ce fichier.
    pause
    exit /b 1
)
if not exist "venv\Scripts\python.exe" (
    echo Premiere fois : creation de l'environnement.
    %PY% -m venv venv
    if errorlevel 1 goto erreur
)

"venv\Scripts\python.exe" -c "import customtkinter, edge_tts, PIL, certifi, soundfile, soxr, sounddevice, numpy" >nul 2>nul
if errorlevel 1 (
    echo Installation des bibliotheques - cela peut prendre quelques minutes...
    "venv\Scripts\python.exe" -m pip install --upgrade pip >nul
    "venv\Scripts\python.exe" -m pip install -r requirements.txt
    if errorlevel 1 goto erreur
)
echo Environnement pret.
echo.

rem ---- 2b. numpy, qui ne se charge pas sur certains PC anciens -----
rem Vu le 3 novembre 2026 sur le PC de Richard (Windows 10 1903) : numpy
rem 2.4.6 installait, puis refusait de se charger (erreur de DLL). numpy
rem 1.26.4 passe sur la meme machine : c'est le repli ci-dessous.
"venv\Scripts\python.exe" -c "import numpy" >nul 2>nul
if errorlevel 1 (
    echo numpy ne se charge pas sur ce PC.
    echo Essai avec numpy 1.26.4...
    "venv\Scripts\python.exe" -m pip install --force-reinstall "numpy==1.26.4"
    "venv\Scripts\python.exe" -c "import numpy" >nul 2>nul
    if errorlevel 1 (
        echo ^>^> numpy ne se charge toujours pas.
        echo    Causes possibles : un antivirus, ou le Visual C++ 2015-2022 absent.
        echo    Installez https://aka.ms/vs/17/release/vc_redist.x64.exe puis relancez.
    ) else (
        echo numpy 1.26.4 se charge : on continue avec celle-ci.
    )
) else (
    echo numpy se charge.
)
echo.

rem ---- 3. Les tests ----------------------------------------------
set "ECHEC=0"
for %%T in (fumee_windows v2_textes v2_ecran v2_langues v2_adaptation v2_paquet) do (
    echo ------------------------------------------------------------
    echo  %%T
    echo ------------------------------------------------------------
    "venv\Scripts\python.exe" "tests\%%T.py"
    if errorlevel 1 (
        set "ECHEC=1"
        echo.
        echo ^>^> ECHEC dans %%T
    )
    echo.
)

if "%ECHEC%"=="1" (
    echo Certains tests ont echoue : copiez le texte ci-dessus.
    echo L'application peut quand meme etre lancee pour regarder.
) else (
    echo Tous les tests sont verts.
)
echo.

rem ---- 4. L'executable (facultatif) -----------------------------
set /p FABRIQUER="Fabriquer dist\Vox-Pack.exe pour verifier le paquet ? (O/N) "
if /i "%FABRIQUER%"=="O" (
    echo Fabrication dans dist\ - quelques minutes...
    "venv\Scripts\python.exe" -m PyInstaller Vox-Pack.spec --noconfirm
    if errorlevel 1 (
        echo ^>^> La fabrication a echoue : copiez le texte ci-dessus.
    ) else (
        if exist "dist\Vox-Pack.exe" (
            echo Cree : dist\Vox-Pack.exe
            for %%F in ("dist\Vox-Pack.exe") do echo   taille : %%~zF octets
        ) else (
            echo ^>^> dist\Vox-Pack.exe est absent.
        )
    )
    echo.
)

rem ---- 5. L'application -------------------------------------------
set /p LANCER="Lancer l'application maintenant ? (O/N) "
if /i "%LANCER%"=="O" (
    "venv\Scripts\python.exe" voxpack2.py
)
pause
exit /b %ECHEC%

:erreur
echo.
echo L'installation a echoue. Verifiez la connexion, puis relancez.
pause
exit /b 1
