import sys, os, confighandler

from ..common import developerconfig

try:
    if sys.argv[1:]:
        discord, openai = sys.argv[1:3]
        if os.path.exists(developerconfig.TOKEN_FILE) == False:
            # TODO: Change system over to yaml format with confighandler.write_api_keys()
            
            with open("dependencies/api-keys.key", "w+") as key_file:
                key_file.writelines([f"{discord}\n", f"{openai}"])

except ValueError:
    print("You did not provide one of the keys. Either both need to be supplied, or leave both fields blank. Starting anyways..")
    exit(1)