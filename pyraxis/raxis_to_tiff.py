#!/usr/bin/env python
"""R-Axis Area Detector image converter

Usage:
  raxis_to_tiff.py [--force] [--format <ext>] [--compress] <oscfile>...

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
import logbook

from pyraxis import read_raxis_file

class ShapeError(Exception):
    """An error encountered while attempting to slice and reshape the
       data to fit the file-specified dimensions."""
    pass


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

    data = read_raxis_file(filename)

    tiff = TIFFimage(data, description='RAXIS file converted to TIFF by raxis_to_image 0.0.3')
    tiff.write_file(newfilename, compression='none' if not compress else 'lzw')
    print('Converted {} to {}'.format(filename, newfilename))


if __name__ == '__main__':
    arguments = docopt(__doc__, version='raxis_to_tiff 0.0.3')
    logbook.debug(arguments)
    for oscfile in arguments['<oscfile>']:
        try:
            convert(oscfile,
                    fileext=arguments['--format'],
                    force=arguments['--force'],
                    compress=arguments['--compress'])
        except ShapeError as serr:
            # Eat exceptions raised as a result of trying to convert
            # damaged files (a diagnostic message is already output
            # by `convert`).
            logbook.error(serr)
