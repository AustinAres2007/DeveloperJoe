@echo off
setlocal enabledelayedexpansion

if not "%1"=="" (
    set "PYTHON_COMMAND=%1"
) else (
    set "PYTHON_COMMAND=python"
)

set "DIR=%~dp0"
cd /d "%DIR%"

where %PYTHON_COMMAND% > nul 2>&1
echo Loading..

if %ERRORLEVEL% EQU 0 (

    for /f "delims=" %%A in ('%PYTHON_COMMAND% -c "import platform; print(platform.python_version())"') do ( 
        set "VERSION=%%A"   
    )
    %PYTHON_COMMAND% "%DIR%\sources\install\py_version.py"    

    if ERRORLEVEL 1 (
        echo You cannot run this script. Python version is too old. ^(Python 3.11 and above. Do the command `%PYTHON_COMMAND% --version` to get your version.^) You can download Python 3.11 at https://python.org
        exit /B
    ) else (
        call Scripts\activate > nul 2>&1
        for /f "delims=" %%A in ('%PYTHON_COMMAND% -c "import sys; print(sys.prefix ^!= sys.base_prefix)"') do ( 
            set "INVIRTUAL=%%A"   
        )
        
        if not "!INVIRTUAL!"=="True" (
            %PYTHON_COMMAND% -m venv %DIR% && call Scripts\activate
            %PYTHON_COMMAND% -m pip install -q --upgrade pip
            %PYTHON_COMMAND% -m pip install -q -r "dependencies\requirements.txt"
        )
        
        if not exist "dependencies\api-keys.yaml" (
            echo "I do not detect a "dependencies/api-keys.yaml" file. You can enter the keys right now. Or leave both prompts blank and a blank key file will be made so you can fill it later. If you have any other files to insert (Voice Libraries) do it now. If not, you can do it later. If you want to exit press "CTRL + C" to do so."

            echo Please enter your Discord Token ^(API Key^) or leave it blank.
            set /p discord_api_key=
            echo Please enter your OpenAI Token ^(API Key^) or leave it blank
            set /p openai_api_key=
        )
        echo Performing bot startup..
        %PYTHON_COMMAND% main.py !discord_api_key! !openai_api_key!
        
    )   
) else (
    echo Python is not installed on this system, or is configured improperly. Given Python Executable: %PYTHON_COMMAND%
)