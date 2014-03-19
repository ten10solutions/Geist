from __future__ import division, absolute_import, print_function

import numpy
import subprocess
import time
import os
import shutil
import struct
from . import logger
from ._x11_common import GeistXBase
from ..core import Location, LocationList


class XwdToNumpyReader(object):
    _XWD_HEADER = struct.Struct('>lllllllhhhhhh')

    def __init__(self, filename):
        self._filename = filename
        self._check_header()

    def _read_dump(self):
        return numpy.fromfile(open(self._filename, 'rb'), numpy.uint8)

    def _check_header(self):
        _, ver, _, planes = XwdToNumpyReader._XWD_HEADER.unpack_from(
            self._read_dump()
        )[:4]
        assert ver == 7, "Only understand xwd version 7"
        assert planes == 24, "Can only handle 24bit screens"

    def _read_w_h_from_header(self, fb):
        return XwdToNumpyReader._XWD_HEADER.unpack_from(fb)[4:6]

    def get_rect(self):
        w, h = self._read_w_h_from_header(self._read_dump())
        return (0, 0, w, h)

    def get_image(self):
        fb = self._read_dump()
        w, h = self._read_w_h_from_header(fb)
        return fb[3232:].reshape((h, w, 4))[:, :, (2, 1, 0)]


class GeistXvfbBackend(GeistXBase):
    _FB_OFFSET = 3232

    def __init__(self, display_num, width=1280, height=1024):
        display = ":%d" % (display_num, )
        self._display_dir = '/var/tmp/Xvfb_display%d' % (display_num,)
        os.makedirs(self._display_dir, 0700)
        dev_null = open('/dev/null', 'w')
        self._xvfb_proc = subprocess.Popen(
            [
                "Xvfb",
                display,
                "-screen",
                "0",
                "%dx%dx24" % (width, height),
                "-fbdir",
                self._display_dir,
            ],
            stdout=dev_null,
            stderr=subprocess.STDOUT
        )
        fb_filepath = '%s/Xvfb_screen0' % (self._display_dir,)
        start_t = time.time()
        while not os.path.exists(fb_filepath):
            if time.time() - start_t > 10:
                raise Exception('Xvfb mmap file did not appear')
        time.sleep(1)
        GeistXBase.__init__(self, display=display)
        self._xwd_reader = XwdToNumpyReader(fb_filepath)

    def capture_locations(self):
        image = self._xwd_reader.get_image()
        h, w = image.shape[:2]
        return LocationList([Location(0, 0, w, h, image=image)])

    def close(self):
        GeistXBase.close(self)
        if hasattr(self, '_xvfb_proc'):
            logger.info("closing geist xvfb")
            self._xvfb_proc.kill()
            shutil.rmtree(self._display_dir, ignore_errors=True)
            del self._xvfb_proc
