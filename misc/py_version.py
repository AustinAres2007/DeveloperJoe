if __name__ == "__main__":
    from platform import python_version_tuple
    MAJOR, MINOR, PATCH = python_version_tuple()
    if int(MAJOR) >= 3:
        if int(MINOR) == 11:
            exit(0)
    print(f"Only compatible with Python 3.11\nYou are using Python {MAJOR}.{MINOR}.{PATCH}")
    exit(1) # MUST BE EXIT CODE 1