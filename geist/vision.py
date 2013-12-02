from __future__ import division
from numpy.fft import fft2, ifft2, irfft2, rfft2
import numpy
import time
import glob
from collections import defaultdict, deque
import itertools
import operator
from functools import partial


def subimage(rect, image):
    x,y,w,h = rect
    return image[y:y+h,x:x+w]


def pad_bin_image_to_shape(image, shape):
    h,w = shape
    ih,iw = image.shape
    assert ih <= h
    assert iw <= w
    if iw < w:
        result = numpy.hstack((image, numpy.zeros((ih,w-iw),bool)))
    else:
        result = image
    if ih < h:
        result = numpy.vstack((result, numpy.zeros((h-ih,w),bool)))
    return result


def sum_2d_images(images):
    it = iter(images)
    result = numpy.copy(next(it))
    for image in it:
        result += image
    return result


OVERLAP_TABLE = (
    (16,(16,8,4,2,1)),
    (15,(15,5,3,1)),
    (12,(12,6,4,3,2,1)),
    (10,(10,5,2,1)),
    (9,(9,3,1)),
    (8,(8,4,2,1)),
    (6,(6,3,2,1)),
    (5,(5,1)),
    (4,(4,2,1)),
    (3,(3,1)),
    (2,(2,1))
)


def best_convolution(
    bin_template, bin_image, tollerance=0.5, overlap_table=OVERLAP_TABLE):
    """
    Selects and applies the best convolution method to find template in image.

    Returns a list of matches in (width, height, x offset, y offset)
    format (where the x and y offsets are from the top left corner).
    """
    count = numpy.count_nonzero(bin_template)
    th,tw = bin_template.shape
    ih,iw = bin_image.shape
    if count == 0 or th == 0 or tw == 0:
        return []
    if th > ih or tw > iw:
        return []
    max_sh = ih // th
    max_sw = iw // th
    overlap_options = [(d, n // d) for n,divs in [(n,divs) for n,divs in overlap_table if ((count+1) ** (n)) < 2**44] for d in divs if d <= max_sh and n // d <= max_sw]
    if not overlap_options:
        return convolution(bin_template, bin_image, tollerance=tollerance)
    best_overlap = sorted(overlap_options, key=lambda x: (ih // x[0] + th) * (iw // x[1] + tw))[0]
    return overlapped_convolution(bin_template, bin_image, tollerance=tollerance, splits=best_overlap)


def convolution(bin_template, bin_image, tollerance=0.5):
    expected = numpy.count_nonzero(bin_template)
    ih,iw = bin_image.shape
    if ih % 2 or iw % 2:
        if ih % 2:
            ih += 1
        if iw % 2:
            iw += 1
        bin_image = pad_bin_image_to_shape(bin_image, (ih,iw))
    if expected == 0:
        return []
    convolution_image = irfft2(rfft2(bin_image) *
                    rfft2(bin_template[::-1,::-1], bin_image.shape))
    h, w = bin_template.shape
    found_bitmap = ((convolution_image > (expected - tollerance)) &
                           (convolution_image < (expected + tollerance)))
    return [((fx - w),  (fy - h))
           for (fy, fx) in numpy.transpose(numpy.nonzero(found_bitmap))]


def overlapped_convolution(bin_template, bin_image, tollerance=0.5, splits=(4,2)):
    th,tw = bin_template.shape
    ih,iw = bin_image.shape
    hs,ws = splits
    h = ih // hs
    w = iw // ws
    count = numpy.count_nonzero(bin_template)
    assert count > 0
    assert h >= th
    assert w >= tw
    yoffset = [(i*h,((i+1)*h) + (th-1)) for i in range(hs)]
    xoffset = [(i*w, ((i+1)*w) + (tw-1)) for i in range(ws)]

    data = [((x1,y1), bin_image[y1:y2,x1:x2], float((count+1) ** (num))) for num, (x1,x2,y1,y2) in enumerate((x1,x2,y1,y2) for (x1,x2) in xoffset for (y1,y2) in yoffset)]

    pad_h = max(i.shape[0] for _,i,_ in data)
    pad_w = max(i.shape[1] for _,i,_ in data)

    # rfft metrics must be an even size - why ... maths?
    if pad_w % 2 == 1:
        pad_w += 1
    if pad_h % 2 == 1:
        pad_h += 1

    overlapped_image = sum_2d_images(pad_bin_image_to_shape(i, (pad_h,pad_w))*num for _,i,num in data)
    #print "Overlap splits %r, Image Size (%d,%d), Overlapped Size (%d,%d)"  % (splits,iw,ih,pad_w,pad_h)
    convolution = numpy.fft.irfft2(numpy.fft.rfft2(overlapped_image) * numpy.fft.rfft2(bin_template[::-1,::-1],overlapped_image.shape))
    results = set()
    for (x,y),_,num in data[::-1]:
        test = convolution / num
        filterd = (test >= (count - tollerance)) & (test <= (count + tollerance))
        for (fy, fx) in numpy.transpose(numpy.nonzero(filterd)):
            results.add((x+fx-tw,y+fy-th))
        convolution %= num
    return list(results)


def get_possible_convolution_regions(bin_template, bin_image, tollerance=0.5,rescale=10):
    result = []
    h,w = bin_template.shape[:2]
    rects = set((x,y,w,h) for x,y in convolution_r3m_targets(bin_template, bin_image, tollerance))
    ih,iw = bin_image.shape[:2]
    aoi = numpy.zeros((ih//rescale+1,iw//rescale+1),bool) # areas of interest
    for x,y,w,h in rects:
        aoi[y//rescale:(y+h)//rescale+1,x//rescale:(x+w)//rescale+1] = True
    bp = binary_partition_image(aoi, min_w = w // rescale, min_h = h // rescale)
    if bp:
        bp = prune_unbeneficial_partitions(aoi, bp)
    return result


def binary_partition_to_rects(bp, image, template_w, template_h, xoffset=0, yoffset=0):
    h,w = image.shape[2:]
    if bp == None:
        return [(xoffset,yoffset,w,h)]
    pos, axis, (p1, p2) = bp
    if axis == 0:
        new_xoffset, new_yoffset = xoffset, yoffset + pos
        i1, i2 = image[pos:], image[:pos]
    else:
        new_xoffset, new_yoffset = xoffset + pos, yoffset
        i1, i2 = image[:,pos:], image[:,:pos]


def prune_unbeneficial_partitions(image, bp):
    pos, axis, (p1, p2) = bp
    if axis == 0:
        i1, i2 = image[pos:], image[:pos]
    else:
        i1, i2 = image[:,pos:], image[:,:pos]
    if p1 is None:
        p1_result = numpy.count_nonzero(i1) == 0
    else:
        p1_result = prune_unbeneficial_partitions(i1, p1)
    if p2 is None:
        p2_result = numpy.count_nonzero(i2) == 0
    else:
        p2_result = prune_unbeneficial_partitions(i2, p2)
    if p1_result or p2_result:
        return [pos, axis, [None if p1_result in [True,False] else p1_result, None if p2_result in [True,False] else p2_result]]
    else:
        return None

def get_partition_scores(image, min_w=1, min_h=1):
    """Return list of best to worst binary splits along the x and y axis.

    """
    h,w = image.shape[:2]
    if w == 0 or h == 0:
        return []
    area = h*w
    cnz = numpy.count_nonzero
    total = cnz(image)
    if total == 0 or area == total:
        return []
    if h < min_h * 2:
        y_c = []
    else:
        y_c = [(-abs((count / ((h-y)*w)) - ((total - count) / (y*w))), y, 0) for count, y in ((cnz(image[y:]), y) for y in range(min_h,image.shape[0]-min_h))]
    if w < min_w * 2:
        x_c = []
    else:
        x_c = [(-abs((count / (h*(w-x))) - ((total - count) / (h*x))), x, 1) for count, x in ((cnz(image[:,x:]), x) for x in range(min_w,image.shape[1]-min_w))]
    return sorted(x_c + y_c)


def get_best_partition(image, min_w=1, min_h=1):
    partitions = get_partition_scores(image, min_w=min_w, min_h=min_h)
    if partitions:
        return partitions[0][-2:]
    else:
        return None


def binary_partition_image(image, min_w=1, min_h=1, depth=0, max_depth=-1):
    """Return a bsp of [pos, axis, [before_node, after_node]] nodes where leaf
    nodes == None.

    If max_depth < 0 this function will continue until all leaf nodes have
    been found, if it is >= 0 leaf nodes will be created at that depth.

    min_w and min_h are the minimum width or height of a partition.

    """
    if max_depth >= 0 and depth >= max_depth:
        return None
    partition = get_best_partition(image, min_w=min_w, min_h=min_h)
    if partition is None:
        return None
    pos, axis = partition
    if axis == 0:
        p1 = binary_partition_image(image[pos:], min_w, min_h, depth+1, max_depth)
        p2 = binary_partition_image(image[:pos], min_w, min_h, depth+1, max_depth)
    elif axis == 1:
        p1 = binary_partition_image(image[:,pos:], min_w, min_h, depth+1, max_depth)
        p2 = binary_partition_image(image[:,:pos], min_w, min_h, depth+1, max_depth)
    return [pos, axis, [p1, p2]]


def draw_binary_partition(image, subdiv, res_image=None, counter=None):
    if res_image is None:
        res_image = numpy.zeros(image.shape)
    if counter is None:
        counter = itertools.count(15)
    pos, axis, (p1, p2) = subdiv
    if axis == 0:
        s1, s2 = res_image[pos:], res_image[:pos]
        i1, i2 = image[pos:], image[:pos]
    else:
        s1, s2 = res_image[:,pos:], res_image[:,:pos]
        i1, i2 = image[:,pos:], image[:,:pos]
    if p1 is None:
        if numpy.count_nonzero(i1):
            s1[:] = next(counter)
    else:
        draw_binary_partition(i1, p1, s1, counter)
    if p2 is None:
        if numpy.count_nonzero(i2):
            s2[:] = next(counter)
    else:
        draw_binary_partition(i2, p2, s2, counter)
    return res_image


def rescale2avg(image):
    sub1 = image[:-1:2,:-1:2]
    sub2 = image[1::2,1::2]
    res = numpy.zeros(sub1.shape, numpy.uint32)
    res += sub1
    res += sub2
    res /= 2
    return res.astype(numpy.uint8)


def rescale2max(image):
    sub1 = image[:-1:2,:-1:2]
    sub2 = image[1::2,1::2]
    if len(image.shape) == 3:
        max_map = grey_scale(sub1) > grey_scale(sub2)
    else:
        max_map = sub1 > sub2
    inv_max_map = max_map == False
    res = numpy.zeros(sub1.shape, numpy.uint8)
    res[max_map] = sub1[max_map]
    res[inv_max_map] = sub2[inv_max_map]
    return res

def rescale3avg(image):
    sub1 = image[:-2:3,:-2:3]
    sub2 = image[1:-1:3,1:-1:3]
    sub3 = image[2::3,2::3]
    res = numpy.zeros(sub1.shape, numpy.uint32)
    res += sub1
    res += sub2
    res += sub3
    res /= 3
    return res.astype(numpy.uint8)


def rescale3max(image):
    sub1 = image[:-2:3,:-2:3]
    sub2 = image[1:-1:3,1:-1:3]
    sub3 = image[2::3,2::3]
    if len(image.shape) == 3:
        grey1 = grey_scale(sub1)
        grey2 = grey_scale(sub2)
        grey3 = grey_scale(sub3)
    else:
        grey1, grey2, grey3 = sub1, sub2, sub3
    max_map_1 = (grey1 > grey2) & (grey1 > grey3)
    max_map_2 = (grey2 > grey1) & (grey2 > grey3)
    max_map_3 = (max_map_1 | max_map_2) == False
    res = numpy.zeros(sub1.shape, numpy.uint8)
    res[max_map_1] = sub1[max_map_1]
    res[max_map_2] = sub2[max_map_2]
    res[max_map_3] = sub3[max_map_3]
    return res


def or_reduce_rescale3max_offset(image):
    return reduce(operator.or_, (rescale3max(image[y1:y2,x1:x2])
        for (y1,y2), (x1,x2) in itertools.product(*[[(i, -(3 - i)) for i in range(3)]]*2)))


def numpy_or_all(images):
    it = iter(images)
    result = numpy.copy(next(it))
    for image in it:
        result |= image
    return result


def grey_scale(image):
    """Converts RGB image to Greyscale

    :param image: input image
    :type image: 3 channel 3d :class:`numpy.ndarray`
    :rtype: :class:`numpy.ndarray`
    """
    return image.astype(numpy.int32).sum(axis=2) // 3


def find_edges(image):
    """Find edges and remove areas on solid colour

    :param image: input image
    :type image: single channel 2d :class:`numpy.ndarray`
    :rtype: :class:`numpy.ndarray`
    """
    return numpy.abs(
        (image[1:,:-1].astype(numpy.int16) - image[1:,1:]) |
        (image[:-1,1:].astype(numpy.int16) - image[1:,1:])
    )

edge_enhance = find_edges


def find_threshold_near_density(img, density, low=0, high=255):
    """Find a threshold where the fraction of pixels above the threshold
    is closest to density where density is (count of pixels above
    threshold / count of pixels).

    The highest threshold closest to the desired density will be returned.

    Use low and high to exclude undesirable thresholds.

    :param img: target image
    :type img: 2d :class:`numpy.ndarray`
    :param density: target density
    :type density: float between 0.0 and 1.0
    :param low: min threshold to test
    :type low: ubyte
    :param migh: max threshold to test
    :type low: ubyte
    :rtype: ubyte

    """
    size = numpy.size(img)
    densities = []
    last_t = None
    while True:
        t = ((high - low) // 2) + low
        if t == last_t:
            densities.sort(key=lambda x: (abs(x[0]-density),256 - x[1]))
            return densities[0][1]
        else:
            last_t = t
        d = numpy.count_nonzero(img > t) / size
        densities.append((d,t))
        if d < density:
            high = t
        elif d >= density: # search away from low
            low = t


def filter_greys_using_image(image, target):
    """Filter out any values in target not in image

    :param image: image containing values to appear in filtered image
    :param target: the image to filter
    :rtype: 2d  :class:`numpy.ndarray` containing only value in image
        and with the same dimensions as target

    """
    maskbase = numpy.array(range(256), dtype=numpy.uint8)
    mask = numpy.where(numpy.in1d(maskbase, numpy.unique(image)),
                                                            maskbase, 0)
    return mask[target]


def correlation_coefficient_normed(template, image):
    h, w = template.shape[:2]
    H, W = image.shape[:2]
    template_size = template.size
    template_distance = template - (template.sum() / template_size)
    corr_num = numpy.zeros((H, W), numpy.float64)
    corr_denum = numpy.zeros((H, W), numpy.float64)
    for y in xrange(H):
        for x in xrange(W):
            image_in_template_area = image[y:y + h, x:x + w]
            image_distance_of_template_area = (
                image_in_template_area - (
                    image_in_template_area.sum() /
                    template_size
                )
            )
            I_H, I_W = image_distance_of_template_area.shape[:2]
            sum_of_template_by_image_distance_at_xy = (
                image_distance_of_template_area * template_distance[:I_H,:I_W]
            ).sum()

            corr_num[y, x] = sum_of_template_by_image_distance_at_xy

            corr_denum[y, x] = numpy.sqrt(
                (template_distance ** 2).sum() *
                (image_distance_of_template_area ** 2).sum()
            )
        print y
    return corr_num / corr_denum

