from sys import platform
from pathlib import Path
from platform import release, machine as arch
from warnings import warn

class OSTypes:
    MacOS = "darwin"
    Windows = "win32"
    Linux = "linux"
    
class Archs:
    arm64 = "arm64"
    x64 = ""
    
def _get_path_according_to_specs(library: str) -> str:
    if platform == OSTypes.Windows and arch().lower() == Archs.arm64:
        warn("You are using an ARM64 Processor on a windows machine. This is not supported. Voice has been disabled.")
        return ""
    return str(Path("voice", platform, release() if platform == "win32" else platform, library).absolute())

def _get_voice_paths(library: str, shared_lib: bool) -> str:
    executable_suffix = {
        OSTypes.Windows: ".exe",
        OSTypes.MacOS: "",
        OSTypes.Linux: ""
    }
    shared_library_suffix = {
        OSTypes.Windows: ".dll",
        OSTypes.MacOS: ".dylib",
        OSTypes.Linux: ".so"
    }
    try:
        path = _get_path_according_to_specs(library)
        if not shared_lib:
            return path + executable_suffix[platform]
        else:
            return path + shared_library_suffix[platform]
    except (KeyError, FileNotFoundError):
        warn("Running an unsupported operating system. Voice will not work.", RuntimeWarning)
        return ""

if __name__ == "__main__":
    _get_voice_paths("ffmpeg", False)
    _get_voice_paths("ffprobe", False)
    _get_voice_paths("opus", True)
    