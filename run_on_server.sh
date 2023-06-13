if [ "$1" != "" ]; then

    git add *
    git commit -m "Updating Version of DJ"
    git push

    echo $1

    ssh samirohim@austinares.synology.me "
        cd ../../../.. && cd volume1/Git && cd developerjoe && 
        git switch test && cd .. && cp -r developerjoe Working && cd developerjoe &&
        git switch wait && cd .. && cd Working/developerjoe && . bin/activate && 
        python3 joe.py > out.log \& && echo Started DeveloperJoe && exit"

    exit
else
    echo "Missing positional arguments: run_on_server.sh {commit message}"
fi
