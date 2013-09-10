#!/usr/bin/env python
"""R-Axis Area Detector image converter

Usage:
  raxis_to_image.py [--force] [--format <ext>] <oscfile>...

Options:
  --format=<ext>    the extension of the filetype to convert the OSC file to
                    (note that this program has only been tested converting
                    to TIFF files) [default: tif]
  --force           overwrite the destination file
"""

from __future__ import division, print_function

from os.path import exists, splitext

from docopt import docopt

from skimage.io import imsave
import numpy as np


class ShapeError(Exception):
    """An error encountered while attempting to slice and reshape the
       data to fit the file-specified dimensions."""
    pass


def interpret(arr):
    """Adapted from libmagic.

       See file-5.14/magic/Magdir/scientific
       available at ftp://ftp.astron.com/pub/file/file-5.14.tar.gz
    """
    # Check the version field to determine the endianess
    if arr[796:800].view('>u4') < 20:
        endian = '>'
    else:
        endian = '<'

    # Width and height must be cast to at least a uint64 to
    # safely multiply them.
    width, height = (long(arr[768:772].view(endian + 'u4')),
                     long(arr[772:776].view(endian + 'u4')))

    print('Interpreting as {}-endian with dimensions {}x{}'
          .format('big' if endian == '>' else 'little', width, height))
    try:
        return (arr.view(endian + 'u2')[-(width * height):]
                .reshape((width, height)))
    except ValueError as err:
        print("""Couldn't convert this array because of a problem interpreting
                 its shape. This file may be corrupt.

                 Some diagnostic information:
                    length of the raw array (in bytes): {}
                    length of the raw array / 4 :       {}
                    width:                              {}
                    heigth:                             {}
                    len / 4 - (width * height):         {}"""
              .format(len(arr), len(arr) / 4, width, height,
                      len(arr) / 4 - (width * height)))
        raise ShapeError(err)


def convert(filename, fileext='tif', force=False):
    """Converts a RAXIS file to an image

       Arguments:
         filename
         fileext - The extension of the filetype to convert to. This is
           passed directly to skimage, so should be some format
           it supports (e.g., 'jpeg', 'tif', 'pbm')
         force - Whether to overwrite an existing image file of the same
           name.
    """
    #### Initial sanity checks
    print("Converting {}".format(filename))

    if fileext == 'osc' or fileext == 'info':
        print("You specified a file extension of '{}'. ".format(fileext) +
              "This would overwrite the original file, possibly before "
              "skimage got really mad because it can't write OSC files."
              "You probably want to specify other options.\nAborting!")
        return

    newfilename = ''.join([splitext(filename)[0], '.', fileext])
    if exists(newfilename):
        if not force:
            print("The file {} already exists. Re-run with --force "
                  "if you want to overwrite it.".format(newfilename))
            return

    #### Attempt to interpret the file
    raw = np.fromfile(filename, dtype='u1')
    if raw[:5].tostring() != 'RAXIS':
        print("This file doesn't seem to be a RAXIS file at all. "
              "(A check that the first five characters are 'RAXIS'"
              " failed). Aborting!")
        return
    data = interpret(raw)

    imsave(newfilename, data)
    print('Converted {} to {}'.format(filename, newfilename))


if __name__ == '__main__':
    arguments = docopt(__doc__, version='raxis_to_image 0.0.1')
    for oscfile in arguments['<oscfile>']:
        try:
            convert(oscfile, fileext=arguments['--format'],
                    force=arguments['--force'])
        except ShapeError:
            # Eat exceptions raised as a result of trying to convert
            # damaged files (a diagnostic message is already output
            # by `convert`).
            pass
