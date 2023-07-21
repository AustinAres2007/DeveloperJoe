#!/bin/sh

PYTHON_COMMAND=python3
DIR=$(cd "$(dirname "$0")"; pwd)

if command -v $PYTHON_COMMAND &> /dev/null
then
    # Retrieve the version number
    VERSION=$($PYTHON_COMMAND -c 'import platform; print(platform.python_version())')
    IFS='.' read -ra VERSION_ARRAY <<< "$VERSION" # Split the version number into its components

    MAJOR=${VERSION_ARRAY[0]}
    MINOR=${VERSION_ARRAY[1]}
    PATCH=${VERSION_ARRAY[2]}

    if [ "$MAJOR" -lt 3 ] || ([ "$MAJOR" -eq 3 ] && [ "$MINOR" -lt 9 ]); then
        echo "You cannot run the install script. Python version is too old. (Python 3.9 and above, you have $VERSION)"
        exit 1
    else
        echo "Valid Python version.. ($VERSION)"
        PYTHON_PATH=$(which $PYTHON_COMMAND)

        echo "Installing virtual enviroment at "$DIR".."
        $PYTHON_PATH -m venv $DIR && . bin/activate
        $PYTHON_COMMAND -m pip install -r dependencies/requirements.txt
        
        if [ ! -e "dependencies/api-keys.key" ]
        then
            echo WARNING: I do not detect a "dependencies/api-keys.key" file.\nI will create one, but no API tokens will be inserted.\nAre you sure you want to continue? (Press anything if so, CTRL + C to exit)
            read -p ""
            touch dependencies/api-keys.key
        fi

        if [ -e "misc/bot_log.log" ] && [ -e "dependencies/histories.db" ]
        then
            echo Finished.
        else
            echo Performing first bot startup..
            $PYTHON_COMMAND "$DIR/joe.py"
        fi

    fi
else
    echo "Python3 is not installed on this system."
fi