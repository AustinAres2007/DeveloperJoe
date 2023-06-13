git add *
git commit -m "Updating Version of DJ"
git push

ssh samirohim@austinares.synology.me "
    pkill -f joe.py && cd ../../../.. && cd volume1/Git && cd developerjoe && 
    git switch test && cd .. && cp -r developerjoe Working && cd developerjoe &&
    git switch wait && cd .. && cd Working/developerjoe && . bin/activate && python3 joe.py > out.log & && exit"
