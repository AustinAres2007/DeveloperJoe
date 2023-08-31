@echo off

setlocal

set "PYTHON_COMMAND=python"
set "DIR=%~dp0"
cd /d "%DIR%"

where %PYTHON_COMMAND% > nul 2>&1
if %errorlevel% == 0 (
    for /f "delims=. tokens=1-3" %%a in ('%PYTHON_COMMAND% -c "import platform; print(platform.python_version())"') do (
        set "MAJOR=%%a"
        set "MINOR=%%b"
        set "PATCH=%%c"
    )

    if %MAJOR% LSS 3 (
        echo You cannot run the install script. Python version is too old. (Python 3.9 and above, you have %MAJOR%.%MINOR%.%PATCH%)
        exit /b 1
    ) else if %MAJOR% EQU 3 (
        if %MINOR% LSS 11 (
            echo You cannot run the install script. Python version is too old. (Python 3.9 and above, you have %MAJOR%.%MINOR%.%PATCH%)
            exit /b 1
        )
    )

    echo Valid Python version.. (%MAJOR%.%MINOR%.%PATCH%)
    set "PYTHON_PATH=%~$PATH:PYTHON_COMMAND%"

    echo Installing virtual environment at "%DIR%"..
    %PYTHON_PATH% -m venv "%DIR%" && call "%DIR%\Scripts\activate.bat"
    %PYTHON_COMMAND% -m pip install -r "%DIR%\dependencies\requirements.txt"

    if not exist "%DIR%\dependencies\api-keys.key" (
        echo WARNING: I do not detect a "dependencies\api-keys.key" file. I will create one, but no API tokens will be inserted. Are you sure you want to continue? (Press anything if so, CTRL + C to exit)
        pause > nul
        type nul > "%DIR%\dependencies\api-keys.key"
    )

    if exist "%DIR%\misc\bot_log.log" if exist "%DIR%\dependencies\dg_database.db" (
        echo.
        echo Finished!
    ) else (
        echo Performing first bot startup..
        %PYTHON_COMMAND% "%DIR%\main.py"
    )
) else (
    echo Python is not installed on this system, or is configured improperly. (Given Python Version: %PYTHON_COMMAND%)
)

endlocal