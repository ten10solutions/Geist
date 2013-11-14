from __future__ import division, absolute_import, print_function

import numpy

from ooxcb.protocol import (
    xproto,
)

from operator import attrgetter
from ._x11_common import GeistXBase


xproto.mixin()


def _bit_c_to_byte(bit_cs):
    res = numpy.copy(bit_cs[0])
    for bit_c in bit_cs[1:]:
        res <<= 1
        res |= bit_c
    return res


class GeistXBackend(GeistXBase):
    def __init__(self, display=':0'):
        GeistXBase.__init__(self, display=display)

    @property
    def rect(self):
        geometry_getter = attrgetter('x', 'y', 'width', 'height')
        return geometry_getter(self._root.get_geometry().reply())

    def capture(self):
        x, y, w, h = self.rect
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
        return res
