from __future__ import division, absolute_import, print_function

import numpy

from ooxcb.protocol import (
    xproto,
)

from operator import attrgetter
from geist.core import Location, LocationList
from ._x11_common import GeistXBase
from . import logger
import pyscreenshot as ImageGrab
import numpy as np
import subprocess
from PIL import Image

xproto.mixin()


def _bit_c_to_byte(bit_cs):
    res = numpy.copy(bit_cs[0])
    for bit_c in bit_cs[1:]:
        res <<= 1
        res |= bit_c
    return res


class GeistXBackend(GeistXBase):
    def __init__(self, **kwargs):
        display = kwargs.get('display', ':0')
        GeistXBase.__init__(self, display=display)
        logger.info("Created GeistXBackend")

    def capture_locations(self):
        geometry_getter = attrgetter('x', 'y', 'width', 'height')
        x, y, w, h = geometry_getter(self._root.get_geometry().reply())
        res = np.array(ImageGrab.grab())
        #subprocess.Popen("import -window root screenshot.png", shell=True).wait()
        #res = np.array(Image.open('screenshot.png'))
        # remove once we have loaded the image as a numpy array
        #subprocess.Popen("rm screenshot.png",shell=True)
        return LocationList([Location(x, y, w, h, image=res)])
