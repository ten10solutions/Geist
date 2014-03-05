from __future__ import division, absolute_import, print_function
import numpy
from PIL import Image
import math
import json
import logging
from scipy.ndimage.measurements import label
from scipy.ndimage import binary_erosion, binary_dilation

logger = logging.getLogger(__name__)

fast_sum = numpy.add.reduce


def calc_ft_x(a):
    return numpy.arange(a.shape[1]), fast_sum(a, 0)


def calc_ft_y(a):
    return numpy.arange(a.shape[0]), fast_sum(a, 1)


def ft_mean(ft):
    return fast_sum(ft[0] * ft[1], None) / fast_sum(ft[1], None)


def ft_moment(ft, num, mn=None):
    if mn is None:
        mn = ft_mean(ft)
    return ft_mean((numpy.power(ft[0] - mn, num), ft[1]))


def ft_skew(ft):
    mn = ft_mean(ft)
    m2 = ft_moment(ft, 2, mn)
    m3 = ft_moment(ft, 3, mn)
    return 0 if m2 == 0 else m3 / m2 ** 1.5


def ft_kurtosis(ft):
    mn = ft_mean(ft)
    m2 = ft_moment(ft, 2, mn)
    m4 = ft_moment(ft, 4, mn)
    return 0 if m2 == 0 else m4 / m2 ** 2.0 - 3


def ft_skew_and_kurtosis(ft):
    ft_0, ft_1 = ft
    ft_1_sum = fast_sum(ft_1, None)
    mn = fast_sum(ft_0 * ft_1, None) / ft_1_sum
    mn_adj = ft_0 - mn
    m2 = fast_sum(numpy.power(mn_adj, 2) * ft_1) / ft_1_sum
    m3 = fast_sum(numpy.power(mn_adj, 3) * ft_1) / ft_1_sum
    m4 = fast_sum(numpy.power(mn_adj, 4) * ft_1) / ft_1_sum
    if m2 == 0:
        return (0, 0)
    else:
        return (m3 / m2 ** 1.5, m4 / m2 ** 2.0 - 3)


def binary_span(bin1d):
    padded = numpy.hstack(([False], bin1d, [False])).astype(numpy.int8)
    diff = padded[1:] - padded[:-1]
    starts, ends = numpy.where(diff == 1), numpy.where(diff == -1)
    return zip(starts[0], ends[0])


def local_minima_character_segmentation(
    arr, min_char_width=2, max_w_h_ratio=1.2
):
    h, w = arr.shape
    dist = fast_sum(arr, 0)
    none_empty_spans = binary_span(dist != 0)
    results = []
    for start, end in none_empty_spans:
        offset = start
        last_split = start
        while offset + (h * max_w_h_ratio) < end:
            offset += min_char_width
            local_part = dist[offset:int(offset + (h * max_w_h_ratio))]
            try:
                split_loc = numpy.where(local_part == local_part.min())[0][0]
            except:
                continue
            offset += split_loc
            results.append((last_split, offset))
            last_split = offset
        if offset < end:
            results.append((last_split, end))
    return results


def max_threshold_character_segmentation(arr, global_max_threshold=0.7):
    global_max = arr.max()
    spans = binary_span(arr.max(0) < global_max * global_max_threshold)
    starts, ends = [], []
    for start, end in spans:
        local_max_along_x = arr[:, start:end].max(0)
        x_min_locations = numpy.where(
            local_max_along_x == local_max_along_x.min()
        )[0]
        min_start, min_stop = x_min_locations[0], x_min_locations[-1]
        starts.append(start + min_start)
        ends.append(start + min_stop + 1)
    return zip(ends, starts[1:])


def threshold_character_segmentation(arr, theshhold):
    return binary_span(fast_sum(arr, 0) > theshhold)


def max_vertical_density_threshold_character_segmentation(
    arr,
    max_v_density_threshold_frac
):
    vertical_densities = fast_sum(arr, 0)
    max_v_dens = vertical_densities.max()
    spans = binary_span(vertical_densities <= (
        max_v_dens * max_v_density_threshold_frac
    ))
    starts, ends = [], []
    for start, end in spans:
        local_max_along_x = arr[:, start:end].max(0)
        x_min_locations = numpy.where(
            local_max_along_x == local_max_along_x.min()
        )[0]
        min_start, min_stop = x_min_locations[0], x_min_locations[-1]
        starts.append(start + min_start)
        ends.append(start + min_stop + 1)
    return zip(ends, starts[1:])


def max_pixel_and_max_vertical_threshold_segmentation(
    arr, pixel_max_threshold_frac=0.7, vertical_max_threshold_frac=0.2
):
    pixel_maxs = arr.max(0)
    max_pixel = pixel_maxs.max()
    vertical_densities = fast_sum(arr, 0)
    max_v_dens = vertical_densities.max()

    bin_array = pixel_maxs < max_pixel * pixel_max_threshold_frac
    bin_array |= (
        vertical_densities <= max_v_dens * vertical_max_threshold_frac
    )

    spans = binary_span(bin_array)
    starts, ends = [], []
    for start, end in spans:
        local_max_along_x = arr[:, start:end].max(0)
        x_min_locations = numpy.where(
            local_max_along_x == local_max_along_x.min()
        )[0]
        min_start, min_stop = x_min_locations[0], x_min_locations[-1]
        starts.append(start + min_start)
        ends.append(start + min_stop + 1)
    return zip(ends, starts[1:])


def empty_span_line_segmentation(arr):
    y_ft = calc_ft_y(arr)
    return binary_span(y_ft[1] != 0)


def create_scaller_adjuster(data):
    mins = numpy.array([min(i) for i in zip(*data)], dtype=numpy.float64)
    maxs = numpy.array([max(i) for i in zip(*data)], dtype=numpy.float64)
    scale = maxs - mins

    def adjuster(d):
        return (d - mins) / scale
    return adjuster


def is_underlined(line):
    a = fast_sum(line, 1)
    l, = a.shape
    third = l // 3
    ratio = fast_sum(a[third * 2:]) / fast_sum(a[third:third * 2])
    return ratio > 1.4


def remove_underline(line):
    a = fast_sum(line, 1)
    l, = a.shape
    y_locations, = numpy.where(a == a.max())
    line_without_underline = numpy.copy(line)
    line_without_underline[y_locations] = 0
    return line_without_underline


def ft_of_rotation(image, angle):
    if angle == 0:
        return calc_ft_y(image)
    elif angle == 90:
        return calc_ft_x(image)
    else:
        return calc_ft_y(rotate_around_mean_center(image, angle))


def rotate_around_mean_center(image, angle, center=None):
    mean_x_center = ft_mean(calc_ft_x(image))
    mean_y_center = ft_mean(calc_ft_y(image))
    h, w = image.shape
    l = max(h, w)
    new = numpy.zeros((2 * l + h, 2 * l + w), numpy.uint8)
    new[l:l + h, l:l + w] = image
    return rotate_around_point(
        new,
        angle,
        (l + mean_x_center, l + mean_y_center)
    )


def rotate_around_point(image, angle, point):
    x, y = point
    a = -math.radians(angle)
    sin, cos = math.sin, math.cos
    transform = (
        cos(a),
        -sin(a),
        x - x * cos(a) + y * sin(a),
        sin(a),
        cos(a),
        y - x * sin(a) - y * cos(a)
    )
    pil_image = Image.fromarray(numpy.uint8(image))
    h, w = image.shape
    rotated_image = pil_image.transform(
        (w, h),
        Image.AFFINE,
        transform,
        Image.BILINEAR
    )
    return numpy.array(rotated_image)


def extract_properties(image):
    ft00 = ft_of_rotation(image, 0)
    ft30 = ft_of_rotation(image, 30)
    ft60 = ft_of_rotation(image, 60)
    ft90 = ft_of_rotation(image, 90)
    s00, k00 = ft_skew_and_kurtosis(ft00)
    s30, k30 = ft_skew_and_kurtosis(ft30)
    s60, k60 = ft_skew_and_kurtosis(ft60)
    s90, k90 = ft_skew_and_kurtosis(ft90)
    return numpy.array([
        ft_mean(ft00) / image.shape[0],
        fast_sum(image, None) / image.max(),
        s00,
        k00,
        s30,
        k30,
        s60,
        k60,
        s90,
        k90,
    ], dtype=numpy.float64)


def split_characters(image, max_w_h_ratio=0.85):
    pimage = process(image)
    for x1, x2 in max_pixel_and_max_vertical_threshold_segmentation(pimage):
        c = pimage[:, x1:x2]
        h, w = c.shape
        if w / h > max_w_h_ratio:
            for x3, x4 in local_minima_character_segmentation(
                c,
                max_w_h_ratio=max_w_h_ratio
            ):
                yield c[:, x3:x4]
        else:
            yield c


def remove_subpixel_aa(image):
    image = image.repeat(3, 0)
    return image.reshape((image.shape[0], -1))


def process(image):
    return (numpy.abs(image[:, :, 1].astype(numpy.int16) -
            image[:, 0:1, 1]).astype(numpy.uint8))


class UnclassifiedCharacterError(Exception):
    pass


def mean_differance(d1, d2):
    return numpy.mean([abs(p2 - p1) for (p1, p2) in zip(d1, d2)])


def distance(d1, d2):
    return sum((p2 - p1) ** 2 for (p1, p2) in zip(d1, d2)) ** 0.5


def first_two_and_not_two_worst_distance(d1, d2):
    diffs = [(p2 - p1) ** 2 for p1, p2 in zip(d1[:2], d2[:2])]
    diffs += sorted((p2 - p1) ** 2 for p1, p2 in zip(d1[2:], d2[2:]))[:-2]
    return fast_sum(diffs) ** 0.5

array_concat = numpy.core.multiarray.concatenate


def best_n_distance_factory(n):
    def best_n_distance(d1, d2):
        diff = (d2[2:] - d1[2:]) ** 2
        diff.sort()
        return numpy.sqrt(
            fast_sum(
                array_concat(((d2[:2] - d1[:2]) ** 2, diff[:n]))
            )
        )
    return best_n_distance


class Classifier(object):
    def __init__(self, cutoff=0.03):
        self._data = []
        self.cut_off = cutoff
        self.distance_func = best_n_distance_factory(6)
        self.extract_func = split_characters
        self.properties_func = extract_properties

    def train(self, image, text, max_w_h_ratio=0.85):
        char_images = list(self.extract_func(image, max_w_h_ratio))
        assert len(char_images) == len(text), (
            "%d == %d" % (len(char_images), len(text))
        )
        for c, im in zip(text, char_images):
            self._data.append(
                (c, self.properties_func(im))
            )
        self._normalize()

    def _normalize(self):
        self._adjuster = create_scaller_adjuster([d for c, d in self._data])
        self._adjusted_data = [(c, self._adjuster(d)) for c, d in self._data]

    def _classify(self, image, max_w_h_ratio=0.85):
        for im in list(self.extract_func(image, max_w_h_ratio)):
            d2 = self._adjuster(self.properties_func(im))
            result = []
            for t, d1 in self._adjusted_data:
                dist = self.distance_func(d1, d2)
                result.append((dist, t))
            yield sorted(result)

    def classify(self, image, unrecognised='ignore', max_w_h_ratio=0.85):
        text = []
        for dists in self._classify(image, max_w_h_ratio):
            d, t = dists[0]
            if d > self.cut_off:
                if unrecognised == 'ignore':
                    text.append('?')
                elif unrecognised == 'error':
                    raise UnclassifiedCharacterError('nearest %r %r' % (d, t))
            else:
                text.append(t)
        return ''.join(text)

    def to_json(self):
        return json.dumps(
            {
                'cut_off': self.cut_off,
                'data': [(c, list(d)) for c, d in self._data]
            }
        )

    def from_json(self, json_string):
        obj = json.loads(json_string)
        self.cut_off = obj['cut_off']
        self._data = [
            (c, numpy.array(d, dtype=numpy.float64)) for c, d in obj['data']
        ]
        self._normalize()

    def _distances(self):
        sorted_data = sorted(self._adjusted_data)
        key = []
        table = []
        for c1, d1 in sorted_data:
            key.append(c1)
            row = []
            for c2, d2 in sorted_data:
                dist = self.distance_func(d1, d2)
                row.append(dist)
            table.append(row)
        return key, table

    def diagnose(self, image, expected_text, max_w_h_ratio=0.85):
        def print_data(d):
            print(''.join('% 9s' % ('%.5f' % (i,),) for i in d))
        print('ypos', 'weight', *[
             i + j for i in ['00', '30', '60', '90'] for j in ['skew', 'kurt']
        ])
        for c, im in zip(expected_text, self.extract_func(image, max_w_h_ratio)):
            ep2 = self.properties_func(im)
            d2 = self._adjuster(ep2)
            print(c)
            print_data(ep2)
            print_data(d2)
            print('_' * 20)
            for (_, ep1), (t, d1) in zip(self._data, self._adjusted_data):
                if t != c:
                    continue
                print(
                    c,
                    self.distance_func(d1, d2),
                    self.distance_func(ep1, ep2)
                )
                print_data(ep1)
                print_data(i1 - i2 for i1, i2 in zip(ep1, ep2))
                print_data(d1)
                print_data(i1 - i2 for i1, i2 in zip(d1, d2))
                print('-' * 20)
            print('=' * 20)
            print()
            
    def match_character(self, character, image, tolerance=0.05):
        character_data = [(char, data) for (char, data) in self._adjusted_data if char == character]
        image_properties = self.properties_func(image)
        adjusted_image_properties = self._adjuster(image_properties)
        if self.distance_func(adjusted_image_properties, character_data[0][1]) < tolerance:
            return True
        else:
            return False

            
    def match_string(self, string, image, tolerance=0.05):
        characters = list(self.extract_func(image))
        if len(string) != len(characters):
            return False
        for i in range(len(string)):
            if not self.match_character(string[i], characters[i], tolerance):
                return False
    
    def contains_string(self, string, image, tolerance=0.5):
        characters = list(self.extract_func(image))
        if len(characters) > len(string):
            number = len(characters) - len(string)
            flag = False
            for i in range(number):
                if self.match_character(string[0], characters[i], tolerance):
                    # set flag to true so we know there's been a macth
                    flag = True
                    # see if rest of string matches
                    for j in range(len(string)-1):
                        if not self.match_character(string[j+1], characters[i+j], tolerance):
                            return False
            if flag:
                # if we've seen a macth and not returned false, then we have a match
                return True
        elif len(string) > len(characters):
            return False
        if self.match_string(string, image, tolerance):
            return True
        return False


def bin_find_span(bin):
    a = numpy.where(bin)[0]
    return a.min(), a.max()


def _create_spans_and_masks(labels, num_labels):
    if num_labels < 1:
        return
    masks = [binary_dilation(labels == i) for i in range(1, num_labels + 1)]
    spans = [bin_find_span(m.sum(0) > 0) for m in masks]
    sorted_spans_and_masks = sorted(zip(spans, masks),
                                    key=lambda x: (x[0][0], -x[0][1]))
    current_span, current_mask = sorted_spans_and_masks[0]
    for span, mask in sorted_spans_and_masks[1:]:
        if span[0] >= current_span[0] and span[1] <= current_span[1]:
            current_mask |= mask
        else:
            yield (current_span,
                   current_mask[:, current_span[0]:current_span[1]])
            current_span, current_mask = span, mask
    yield current_span, current_mask[:, current_span[0]:current_span[1]]


def character_seg_max_vertical_sum(grey_scale_image, fraction=0.05):
    for x1, x2 in max_vertical_density_threshold_character_segmentation(
        grey_scale_image,
        fraction
    ):
        yield grey_scale_image[:, x1:x2]


def character_seg_erosion(grey_scale_image, max_w_h_ratio=0.85):
    bin_img = grey_scale_image > 0
    labels, num_labels = label(binary_erosion(bin_img > 0))
    for span, mask in _create_spans_and_masks(labels, num_labels):
        char_img = grey_scale_image[:, span[0]:span[1]].copy()
        char_img[mask == False] = 0
        yield char_img
