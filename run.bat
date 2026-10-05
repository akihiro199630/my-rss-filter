@echo off
setlocal
cd /d "%~dp0"

if not defined TARGET_ALT_TEXT set "TARGET_ALT_TEXT=スポニチ,スポーツ報知"
echo TARGET_ALT_TEXT=%TARGET_ALT_TEXT%

if not defined SOURCE_RSS_URL (
    echo ERROR: Set SOURCE_RSS_URL to the full source RSS URL before running this batch.
    exit /b 1
)

where py >nul 2>nul
if errorlevel 1 (
    set "PYTHON=python"
) else (
    set "PYTHON=py -3"
)

if not exist ".venv\Scripts\python.exe" (
    %PYTHON% -m venv .venv
    if errorlevel 1 (
        echo ERROR: Could not create the virtual environment.
        exit /b 1
    )
)

".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Could not install requirements.
    exit /b 1
)

".venv\Scripts\python.exe" generate_rss.py
if errorlevel 1 (
    echo ERROR: RSS generation failed.
    exit /b 1
)

if not exist "public\filtered_rss.xml" (
    echo ERROR: public\filtered_rss.xml was not generated.
    exit /b 1
)

for %%F in ("public\filtered_rss.xml") do (
    if %%~zF LEQ 0 (
        echo ERROR: public\filtered_rss.xml is empty.
        exit /b 1
    )
)

echo SUCCESS: public\filtered_rss.xml was generated and is not empty.
exit /b 0
