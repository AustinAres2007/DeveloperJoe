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
    call Scripts\activate > nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        for /f "delims=" %%A in ('%PYTHON_COMMAND% -c "import sys; print(sys.prefix ^!= sys.base_prefix)"') do ( 
            set "INVIRTUAL=%%A"   
        )
        if "!INVIRTUAL!"=="True" (
            echo Running normally.
            %PYTHON_COMMAND% main.py
        ) else (
            echo Incorrect / missing virtual enviroment. ^(0^)
        )
    ) else (
        echo Incorrect / missing virtual enviroment. ^(1^)
    )
    
) else (
    echo Python is not installed on this system, or is configured improperly. Given Python Executable: %PYTHON_COMMAND%
)
