"""Downloads DG Libraries depending upon computer specifications."""
import requests, os, shutil

from platform import machine
from sys import platform

arch = machine().lower()

libs = {
    "arm64": {
        "darwin": "https://github.com/AustinAres2007/developerjoe-downloads/releases/download/v1.0.3-mac/macos-arm64.zip",
        "linux": "https://github.com/AustinAres2007/developerjoe-downloads/releases/download/v1.0.1-linux/linux-arm64.zip"   
    },
    "x86_64": {
        "linux": "https://github.com/AustinAres2007/developerjoe-downloads/releases/download/v1.0.1-linux/linux-amd64.zip",
        "win32": "https://github.com/AustinAres2007/developerjoe-downloads/releases/download/1.0.0-win/windows-amd64.zip"
    }
}
    
def download_file(url: str) -> str | None:
    """Downloads a specified file from the internet.

    Args:
        url (str): The URL of the download.

    Returns:
        str: The path of the file locally.
    """
    
    if len(os.listdir("voice/")) < 3:
        
        filename = os.path.split(url)[1]
        voice_zip_location = f"voice/{filename}"
        without_ext = os.path.splitext(voice_zip_location)[0]
        
        print(f"Downloading {url} to {voice_zip_location}..")
        
        if not os.path.exists(voice_zip_location):
            with open(voice_zip_location, "wb") as lib_file:
                with requests.get(url, allow_redirects=True) as req:
                    if req.status_code == 200:
                        lib_file.write(req.content)
                    else:
                        print("Invalid voice download link. Perhaps it is old?")
                        os.remove(voice_zip_location)
                        return 
                        
        print(f"Extracting to {without_ext}..")   
        shutil.unpack_archive(voice_zip_location, "voice/")
        
        print(f"Moving from {without_ext} to voice/")
        for f in os.listdir(without_ext):
            shutil.move(f"{without_ext}/{f}", "voice/")
        
        os.remove(voice_zip_location)
        shutil.rmtree(without_ext)
        
        print("Finished Downloading Voice Libraries.")
        return voice_zip_location
    else:
        print("Voice libraries already installed.")
    
def get_download_path() -> str | None:
    """Gets the applicable library download link according to computer specifications" 

    Returns:
        str: The URL.
    """
    try:
        return libs[arch][platform]
    except KeyError:
        print("Your system does not support voice.")

if __name__ == "__main__":
    path = get_download_path()
    if path:
        download_file(path)