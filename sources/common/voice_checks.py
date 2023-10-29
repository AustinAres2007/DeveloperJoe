from sys import platform
from pathlib import Path
from platform import machine 
from warnings import warn
from os import system

arch = machine().lower()

class OSTypes:
    MacOS = "darwin"
    Linux = "linux"
    Unix = (Linux, MacOS)
    
class Archs:
    arm64 = "arm64"
    x64 = ""
    
def _get_path_according_to_specs(library: str) -> str:
    if platform == OSTypes.MacOS and arch == Archs.x64:
        warn("You are using an Intel processor on a Mac machine. This is not supported. Voice has been disabled.")
    elif platform == OSTypes.Linux and arch == Archs.arm64:
        warn("Somehow you are using an ARM64 processor on Linux. This is not supported. Voice has been disabled.")
    else:
        return str(Path("voice", f"{library}-{platform}").absolute())
        #return str(Path("voice", platform, release() if platform == "win32" else platform, library).absolute()) Old
    return ""

def _get_voice_paths(library: str, shared_lib: bool) -> str:
    executable_suffix = {
        OSTypes.MacOS: "",
        OSTypes.Linux: ""
    }
    shared_library_suffix = {
        OSTypes.MacOS: ".dylib",
        OSTypes.Linux: ".so"
    }
    
    try:
        path = _get_path_according_to_specs(library)
        final_path = path + executable_suffix[platform] if not shared_lib else path + shared_library_suffix[platform]
        
        system(f"chmod a+rwx {final_path}")
        return final_path
    
    except (KeyError, FileNotFoundError):
        warn("Running an unsupported operating system. Voice will not work.", RuntimeWarning)
        return ""

if __name__ == "__main__":
    ffm = _get_voice_paths("ffmpeg", False)
    ffp = _get_voice_paths("ffprobe", False)
    opus = _get_voice_paths("opus", True)
    
    print(ffm, ffp, opus)
    