import errno
import os

# This function is frequently useful - its definition is from
# http://stackoverflow.com/q/600268/223092

def mkdir_p(path):
    """Ensure that a directory (including its parents) exists

    This should not fail if the directory already exists:

    >>> from tempfile import mkdtemp
    >>> tmp_root = mkdtemp()
    >>> from os.path import join, isdir
    >>> new_directory = join(tmp_root, 'foo', 'bar')
    >>> mkdir_p(new_directory)
    >>> isdir(new_directory)
    True
    >>> mkdir_p(new_directory)

    But if the directory can't be created (e.g. because a file is there
    instead there should be an exception:

    >>> inconvenient_file = join(tmp_root, 'foo', 'quux')
    >>> with open(inconvenient_file, 'w'): pass
    >>> mkdir_p(inconvenient_file) # doctest: +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
      ...
    OSError:

    Finally, remove the test data that we just created:

    >>> import shutil
    >>> shutil.rmtree(tmp_root)
    """
    try:
        os.makedirs(path)
    except OSError as exc: # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise
