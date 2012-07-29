import os.path

def findFile(fname, path=[]):
    """Finds file from path (always including the current working directory) and returns
    its path or 'None' if the file does not exist.
    If path is not given or an empty list, only checks if the file is present locally.

    On Windows, this also chagnges forward slashes to backward slashes in the path."""

    if os.path.exists(fname):
        return fname

    for p in path:
        testpath = os.path.join(os.path.normpath(p), fname)
        if os.path.exists(testpath):
            return testpath

    return None
