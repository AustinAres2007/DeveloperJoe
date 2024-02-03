# Assists with the `install.bat` script.

if __name__ == "__main__":
    from platform import python_version_tuple
    MAJOR, MINOR, PATCH = python_version_tuple()
    if int(MAJOR) >= 3:
        if int(MINOR) >= 12:
            exit(0)
    exit(1) # MUST BE EXIT CODE 1