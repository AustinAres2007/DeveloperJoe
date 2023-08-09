#!/bin/sh

if [[ "$1" =~ python.* ]]
then
    PYTHON_COMMAND=$1
else
    PYTHON_COMMAND=python3
fi

echo Using \"$PYTHON_COMMAND\"
DIR=$(cd "$(dirname "$0")"; pwd)
cd $DIR

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
        $PYTHON_PATH -m venv $DIR && . "$DIR/bin/activate"
        $PYTHON_COMMAND -m pip install -r "$DIR/dependencies/requirements.txt"
        
        echo "Do you want to install CoQui-TTS? It is a text-to-speach system that sounds very life-like, and will be used for speach replies if the user enables it.\n\nDespite that, I ask you to proceed with caution. CoQui can be unstable on many systems, take up significant resources and HDD Space.\n\n('y' to continue, anything else to decline the install.)"
        read WANTSVOICE

        if [ "$WANTSVOICE" = "y" ]
        then
            $PYTHON_COMMAND -m pip install -r "$DIR/dgsetup/requirements-voice.txt"
            $PYTHON_COMMAND -m pip install mecab-python3 unidic-lite
            $PYTHON_COMMAND "$DIR/dgsetup/installcoqui.py"
        fi

        if [ ! -e "$DIR/dependencies/api-keys.key" ]
        then
            echo "WARNING: I do not detect a "dependencies/api-keys.key" file. I will create one, but no API tokens will be inserted. Are you sure you want to continue? (Press anything if so, CTRL + C to exit)"
            read -p ""
            touch "$DIR/dependencies/api-keys.key"
        fi

        if [ -e "$DIR/misc/bot_log.log" ] && [ -e "$DIR/dependencies/dg_database.db" ]
        then
            echo "\n\nFinished!"
        else
            echo Performing first bot startup..
            $PYTHON_COMMAND "$DIR/joe.py"
        fi

    fi
else
    echo "Python is not installed on this system, or is configured improperly. (Given Python Version: $PYTHON_COMMAND)"
fi