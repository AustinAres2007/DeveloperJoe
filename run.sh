#!/bin/sh

PYTHON_COMMAND=python3
DIR=$(cd "$(dirname "$0")"; pwd)
cd $DIR
IN_VE=$(python3 -c 'import sys; print(sys.prefix != sys.base_prefix)')

if [ -e "$DIR/bin/activate" ]
then
    source $DIR/bin/activate
    if [ "$IN_VE" = "True" ]
    then
        if [ "$1" != "1" ]; then 
            echo "Running normally."
            $PYTHON_COMMAND main.py
        else
            echo "Running indefinitly. Use the '/shutdown' bot command to halt execution."
            $PYTHON_COMMAND main.py &
        fi
    else
        echo "Incorrect / missing virtual enviroment. (0)"
    fi
else
    echo "Missing virtual enviroment. (1)"
fi