from __future__ import division, absolute_import, print_function

import numpy

from ooxcb.protocol import (
    xproto,
)

from operator import attrgetter
from geist.core import Location, LocationList
from ._x11_common import GeistXBase
from . import logger


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
        raw_img = self._root.get_image(
            xproto.ImageFormat.XYPixmap,
            x,
            y,
            w,
            h,
            0xFFFFFFFF
        ).reply().data
        im = numpy.unpackbits(
            numpy.array(raw_img, numpy.uint8).reshape(3, 8, h, w // 8, 1),
            4
        )[:, :, :, :, ::-1].reshape(3, 8, h, w)
        res = numpy.zeros((h, w, 3), numpy.uint8)
        res[:, :, 0] = _bit_c_to_byte(im[0])
        res[:, :, 1] = _bit_c_to_byte(im[1])
        res[:, :, 2] = _bit_c_to_byte(im[2])
        return LocationList([Location(x, y, w, h, image=res)])
