from __future__ import division
import numpy


def filter(colour_filter):
    def apply_filter(image):
        result = numpy.copy(image)
        result[colour_filter(image) == False] = [0, 0, 0]
        return result
    return apply_filter


def hsv(func):
    def hsv_call(image):
        return func(*rgb_to_hsv(image))
    return hsv_call

RED = hsv(lambda h, s, v: ((h >= 216) | (h <= 32)) & (s > 128) & (v > 15))
YELLOW = hsv(lambda h, s, v: ((h >= 32) & (h <= 48)) & (s > 128) & (v > 15))
GREEN = hsv(lambda h, s, v: ((h >= 48) & (h <= 112)) & (s > 128) & (v > 15))
AQUA = hsv(lambda h, s, v: ((h >= 120) & (h <= 132)) & (s > 128) & (v > 15))
BLUE = hsv(lambda h, s, v: ((h >= 132) & (h <= 200)) & (s > 128) & (v > 15))
PURPLE = hsv(lambda h, s, v: ((h >= 200) & (h <= 216)) & (s > 128) & (v > 15))
WHITE = hsv(lambda h, s, v: ((s < 5) & (v > 250)))


def rgb(func):
    def rgb_call(image):
        return func(image[:, :, 0], image[:, :, 1], image[:, :, 2])
    return rgb_call


def rgb_to_hsv(image):
    min_rgb = image.min(axis=2)
    max_rgb = image.max(axis=2)

    diff_rgb = (max_rgb - min_rgb)

    #value
    val = max_rgb

    #saturation
    sat_div = numpy.copy(val)
    sat_div[sat_div == 0] = 255  # avoid div by zero

    _ = diff_rgb.astype(numpy.float32)
    _ *= 255
    _ /= sat_div
    sat = _.astype(numpy.uint8)
    sat[val == 0] = 0

    #hue
    r = image[:, :, 0]
    g = image[:, :, 1]
    b = image[:, :, 2]

    hue_div = numpy.copy(diff_rgb)
    hue_div[hue_div == 0] = 255  # avoid div by zero

    hue_r = (((g.astype(numpy.float32) - b) / hue_div) * 43
             ).astype(numpy.uint8)
    hue_r[r != max_rgb] = 0
    hue_g = ((((b.astype(numpy.float32) - r) / hue_div) * 43) + 85
             ).astype(numpy.uint8)
    hue_g[g != max_rgb] = 0
    hue_b = ((((r.astype(numpy.float32) - g) / hue_div) * 43) + 171
             ).astype(numpy.uint8)
    hue_b[b != max_rgb] = 0
    hue = hue_r | hue_g | hue_b
    hue[diff_rgb == 0] = 0

    return hue, sat, val


__all__ = ["filter", "hsv", "rgb", "rgb_to_hsv"]
