from __future__ import division
import numpy
import math
import colorsys


def colour_wheel(size=255):
    if hasattr(colour_wheel, 'last') and colour_wheel.last[0] == size:
        return colour_wheel.last[1]
    result = numpy.zeros((size, size, 3), numpy.uint8)
    r = cy = cx = size / 2
    for y in range(size):
        for x in range(size):
            dist = numpy.sqrt(numpy.abs(((x - cx) ** 2) + ((y - cy) ** 2)))
            v = 1 - ((dist - (r / 2)) / (r / 2))
            s = (dist / (r / 2))
            v = v if v >= 0 else 0
            v = v if v <= 1 else 1
            s = s if s <= 1 else 1
            h = (math.atan2((y - cy), (x - cx))) / (2 * math.pi)
            h %= 1
            result[y, x] = numpy.array(colorsys.hsv_to_rgb(h, s, v)) * 255
    colour_wheel.last = (size, result)
    return result


def greys_chart(w=50, h=200):
    result = numpy.zeros((h, w, 3), numpy.uint8)
    for y in range(h):
        result[y, :, :] = 255 * ((y + 1) / h)
    return result


def colours_chart(w=50, h=200):
    result = numpy.zeros((h, w, 3), numpy.uint8)
    for y in range(h):
        result[y, :, :] = numpy.array(
            colorsys.hsv_to_rgb((y + 1) / h, 1, 1)) * 255
    return result
