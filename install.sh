PYTHON_COMMAND=python3
if command -v $PYTHON_COMMAND &> /dev/null
then
    PYTHON=$(which $PYTHON_COMMAND)
    echo $PYTHON
    echo $(ls)
else
    echo "Python3 is not installed on this system."
fi