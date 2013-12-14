#!/usr/bin/env python
"""R-Axis Area Detector image converter

Usage:
  raxis_to_image.py [--force] [--format <ext>] [--compress] <oscfile>...

Options:
  --format=<ext>    the extension of the filetype to convert the OSC file to
                    (must be either 'tif' or 'tiff' at present; support for
                    other 16-bit filetypes may be added in future)
                    [default: tif]
  --force           overwrite the destination file
  --compresss       whether to use LZW compression for the TIFF file;
                    [default: False]
"""

from __future__ import division, print_function

from os.path import exists, splitext

from docopt import docopt

from libtiff import TIFFimage
import numpy as np


class ShapeError(Exception):
    """An error encountered while attempting to slice and reshape the
       data to fit the file-specified dimensions."""
    pass


def interpret(arr):
    """Adapted from libmagic.

       See file-5.14/magic/Magdir/scientific
       available at ftp://ftp.astron.com/pub/file/file-5.14.tar.gz

       Returns
       -------
       arr : ndarray
         2-dimensional uint16 array of RAXIS detector data
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


def convert(filename, fileext='tif', force=False, compress=False):
    """Converts a RAXIS file to an image

       Arguments
       ---------
       filename : string
       fileext : string
         Either 'tif' or 'tiff'; since RAXIS data is 16-bit, it is of
         dubious utility to use other formats. Support for other 16-bit
         formats may be added in future
       force : string
         Whether to overwrite an existing image file of the same
         name.
    """
    #### Initial sanity checks
    print("Converting {}".format(filename))

    if fileext not in ['tif', 'tiff']:
        print("RAXIS data is 16-bit; at the moment, we therefore only support "
              "saving it to TIFF files.")
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

    tiff = TIFFimage(data, description='RAXIS file converted to TIFF by raxis_to_image 0.0.2')
    tiff.write_file(newfilename, compression='none' if not compress else 'lzw')
    print('Converted {} to {}'.format(filename, newfilename))


if __name__ == '__main__':
    arguments = docopt(__doc__, version='raxis_to_image 0.0.2')
    print(arguments)
    for oscfile in arguments['<oscfile>']:
        try:
            convert(oscfile,
                    fileext=arguments['--format'],
                    force=arguments['--force'],
                    compress=arguments['--compress'])
        except ShapeError:
            # Eat exceptions raised as a result of trying to convert
            # damaged files (a diagnostic message is already output
            # by `convert`).
            pass
