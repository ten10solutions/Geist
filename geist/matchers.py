from .match_position_finder_helpers import get_tiles_at_potential_match_regions, normalise_correlation, normalise_correlation_coefficient
from scipy.signal import fftconvolve
from scipy.ndimage.measurements import label, find_objects
import numpy as np

# both these methods return array of points giving bottom right coordinate of match

def match_via_correlation(image, template, raw_tolerance=1, normed_tolerance=0.9):
    """ Matchihng algorithm based on normalised cross correlation.
        Using this matching prevents false positives occuring for bright patches in the image
    """
    h, w = image.shape
    th, tw = template.shape
    # fft based convolution enables fast matching of large images
    correlation = fftconvolve(image, template[::-1,::-1])
    # trim the returned image, fftconvolve returns an image of width: (Temp_w-1) + Im_w + (Temp_w -1), likewise height
    correlation = correlation[th-1:h, tw-1:w]
    # find images regions which are potentially matches
    match_position_dict = get_tiles_at_potential_match_regions(image, template, correlation, raw_tolerance=raw_tolerance)
    # bright spots in images can lead to false positivies- the normalisation carried out here eliminates those
    results = normalise_correlation(match_position_dict, correlation, template, normed_tolerance=normed_tolerance)
    return results




def match_via_correlation_coefficient(image, template, raw_tolerance=1, normed_tolerance=0.9):
    """ Matching algorithm based on 2-dimensional version of Pearson product-moment correlation coefficient.

        This is more robust in the case where the match might be scaled or slightly rotated.

        From experimentation, this method is less prone to false positives than the correlation method.
    """
    h, w = image.shape
    th, tw = template.shape
    temp_mean = np.mean(template)
    temp_minus_mean = template - temp_mean
    convolution = fftconvolve(image, temp_minus_mean[::-1,::-1])
    convolution = convolution[th-1:h, tw-1:w]
    match_position_dict = get_tiles_at_potential_match_regions(image, template, convolution, method='correlation coefficient', raw_tolerance=raw_tolerance)
    # this is empty, so think condition is wrong
    results = normalise_correlation_coefficient(match_position_dict, convolution, template, normed_tolerance=normed_tolerance)
    return results




def fuzzy_match(image, template, normed_tolerance=None, raw_tolerance=None, method='correlation'):
    """Determines, using one of two methods, whether a match(es) is present and returns the positions of
       the bottom right corners of the matches.
       Fuzzy matches returns regions, so the center of each region is returned as the final match location

       USE THIS FUNCTION IF you need to match, e.g. the same image but rendered slightly different with respect to
       anti aliasing; the same image on a number of different backgrounds.

       The method is the name of the matching method used, the details of this do not matter. Use the default method
       unless you have too many false positives, in this case, use the method 'correlation coefficient.' The
       correlation coefficient method can also be more robust at matching when the match might not be exact.

       The raw_tolerance is the proportion of the value at match positions (i.e. the value returned for an exact match)
       that we count as a match. For fuzzy matching, this value will not be exactly the value returned for an exact match
       N. B. Lowering raw_tolerance increases the number of potential match tiles requiring normalisation.
       This DRAMATICALLY slows down matching as normalisation (a process which eliminates false positives)

       The normed_tolerance is how far a potential match value can differ from one after normalisation.

       The tolerance values indicated below are from a short investigation, looking to minimise missing items we wish to match,
       as all as false positives which inevitably occur when performing fuzzy matching. To generate these values, we
       tested maching letters with different type of antialiasing on a number of backgrounds.
    """
    if method == 'correlation':
        if not raw_tolerance:
            raw_tolerance = 0.85
        if not normed_tolerance:
            normed_tolerance = 0.85
        results = np.array(match_via_correlation(image, template, raw_tolerance=raw_tolerance, normed_tolerance=normed_tolerance))
    elif method == 'correlation coefficient':
        if not raw_tolerance:
            raw_tolerance = 0.8
        if not normed_tolerance:
            normed_tolerance = 0.9
        results = np.array(match_via_correlation_coefficient(image, template, raw_tolerance=raw_tolerance, normed_tolerance=normed_tolerance))
    h, w = image.shape
    th, tw = template.shape
    results = np.array([(result[0] + th -1, result[1] + tw -1) for result in results])
    #match_x, match_y = int(np.mean(results[:,1])), int(np.mean(results[:,0]))
    results_aggregated_mean_match_position = match_positions((h,w), results)
    return results_aggregated_mean_match_position

    #return results


def match_positions(shape, list_of_coords):
    """ In cases where we have multiple matches, each highlighted by a region of coordinates,
        we need to separate matches, and find mean of each to return as match position
    """
    match_array = np.zeros(shape)
    try:
        # excpetion hit on this line if nothing in list_of_coords- i.e. no matches
        match_array[list_of_coords[:,0],list_of_coords[:,1]] = 1
        labelled = label(match_array)
        objects = find_objects(labelled[0])
        coords = [{'x':(slice_x.start, slice_x.stop),'y':(slice_y.start, slice_y.stop)} for (slice_y,slice_x) in objects]
        final_positions = [(int(np.mean(coords[i]['y'])),int(np.mean(coords[i]['x']))) for i in range(len(coords))]
        return final_positions
    except IndexError:
        print 'no matches found'
        # this error occurs if no matches are found
        return []


## not what we want a all!!! only will take exact matches, defeating entire point
def post_process(image, template, list_of_coords):
    h, w = template.shape
    for x, y in list_of_coords:
        print x-h + 1, y-w + 1
        sub_image = image[x-h + 1:x + 1, y-w + 1:y + 1]
        print sub_image.shape, template.shape, x, y
        if not np.allclose(template, sub_image):
            list_of_coords.remove((x,y))
    return list_of_coords


def to_rgb(im):
    return np.dstack([im.astype(np.uint8)] * 3).copy(order='C')


def highlight_matched_region_no_normalisation(image, template, method='correlation', normed_tolerance=0.666):
    conv = fftconvolve(image, template[::-1,::-1])
    th, tw = template.shape
    r = find_potential_match_regions(template, conv, method=method, normed_tolerance=normed_tolerance)
    r_in_image = [(r_x, r_y) for (r_x, r_y) in r if (r_x < image.shape[0] and r_y < image.shape[1])]
    im_rgb = to_rgb(image)
    for (x,y) in r_in_image:
        try:
            im_rgb[x-th:x,y-tw:y] = 0, 100, 100
        except IndexError:
            im_rgb[x,y] = 0, 100, 100
    return im_rgb


def highlight_matched_region_normalised(image, shape, list_of_coords):
    th, tw = shape
    im_rgb = to_rgb(image)
    for (x,y) in list_of_coords:
        #print (x,y)
        try:
            im_rgb[x-th:x,y-tw:y] = 0, 100, 100
        except IndexError:
            im_rgb[x,y] = 0, 100, 100
    return im_rgb
