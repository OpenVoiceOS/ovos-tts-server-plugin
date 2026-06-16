# START_VERSION_BLOCK
VERSION_MAJOR = 0
VERSION_MINOR = 0
VERSION_BUILD = 6
VERSION_ALPHA = 1
# END_VERSION_BLOCK


def _build_version():
    version = f"{VERSION_MAJOR}.{VERSION_MINOR}.{VERSION_BUILD}"
    if VERSION_ALPHA:
        version += f"a{VERSION_ALPHA}"
    return version


__version__ = _build_version()
