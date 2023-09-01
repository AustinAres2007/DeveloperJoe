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

if %ERRORLEVEL% EQU 0 (

    for /f "delims=" %%A in ('%PYTHON_COMMAND% -c "import platform; print(platform.python_version())"') do ( 
        set "VERSION=%%A"   
    )
    %PYTHON_COMMAND% "%DIR%\misc\py_version.py"
    if ERRORLEVEL 1 (
        exit /B
    ) else (
        echo Valid Python version.. ^(!VERSION!^)
        echo Installing virtual enviroment at "%DIR%"..

        %PYTHON_COMMAND% -m venv %DIR% && call Scripts\activate
        %PYTHON_COMMAND% -m pip install -r "dependencies\requirements.txt"

        if not exist "dependencies\api-keys.key" (
            echo ^WARNING: I do not detect a "dependencies/api-keys.key" file. I will create one, but no API tokens will be inserted. Are you sure you want to continue? ^(Type "Y" to continue, anything else to cancel.^)
            set /p continue=
            if not "!continue!"=="Y" (
                echo Stopping...
                exit /B
            ) else (
                type nul > dependencies\api-keys.key
            )
        )
        if exist "misc\bot_log.log" (
            if exist "dependencies\dg_database.db" (
                echo Finished!
                exit /B
            )
            
        ) 
        echo Performing first bot startup..
        %PYTHON_COMMAND% main.py
        
    )   
) else (
    echo Python is not installed on this system, or is configured improperly. Given Python Executable: %PYTHON_COMMAND%
)