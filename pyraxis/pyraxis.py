"""Functions to load a RAXIS file as a Numpy ndarray"""
from __future__ import division, print_function

import numpy as np

import logbook


class ShapeError(IOError):

    """An error encountered while attempting to slice and reshape the
       data to fit the file-specified dimensions."""

    def __init__(self, message, original_exception=None):
        self.message, self.original_exception = message, original_exception

    def __str__(self):
        return self.message


def _interpret(arr):
    """Adapted from libmagic.

       See file-5.14/magic/Magdir/scientific
       available at ftp://ftp.astron.com/pub/file/file-5.14.tar.gz

       Parameters
       ----------
       arr : ndarray
         1-dimensional ndarray of dtype uint8 containing the
         whole RAXIS file

       Returns
       -------
       arr : ndarray
         2-dimensional uint16 array of RAXIS detector data
    """
    # Check the version field to determine the endianess
    endian = '>' if arr[796:800].view('>u4') < 20 else '<'

    # Width and height must be cast to at least a uint64 to
    # safely multiply them. (Otherwise default numpy rules
    # result in multiplication modulo 2 ** 32.)
    width, height = (long(arr[768:772].view(endian + 'u4')),
                     long(arr[772:776].view(endian + 'u4')))

    logbook.info('Interpreting as {}-endian with dimensions {}x{}'
                 .format('big' if endian == '>' else 'little',
                         width, height))

    diagnostics = """
Diagnostic information:
    length of the raw array (in bytes): {}
    length of the raw array / 4 :       {}
    width:                              {}
    heigth:                             {}
    len / 4 - (width * height):         {}
""".format(len(arr), len(arr) / 4, width, height,
           len(arr) / 4 - (width * height))

    logbook.debug(diagnostics)

    try:
        return (arr.view(endian + 'u2')[-(width * height):]
                .reshape((width, height)))
    except ValueError as err:
        serr = ShapeError(
            """Couldn't convert this array because of a problem interpreting
               its shape. This file may be corrupt.
            """ + diagnostics)
        serr.original_exception = err
        raise serr


def read_raxis_file(filename):
    """Reads a RAXIS file into an ndarray

       Parameters
       ----------
       filename : string
         The filename to read.

       Returns
       -------
       arr : ndarray
         2-dimensional ndarray of dtype uint16
    """
    # Attempt to interpret the file
    raw = np.fromfile(filename, dtype='u1')
    if raw[:5].tostring() != 'RAXIS':
        raise IOError("This file doesn't seem to be a RAXIS file at all. "
                      "(A check that the first five characters are 'RAXIS'"
                      " failed). Aborting!")
    return _interpret(raw)
