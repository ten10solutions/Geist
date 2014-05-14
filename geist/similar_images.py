 # want to build a function which finds out if any image in repository is 'similar' to existing image.
# use convolution
from geist.vision import pad_bin_image_to_shape, grey_scale, find_edges
import numpy
from numpy.fft import irfft2, rfft2

def binarise_image(image):
    if len(image.shape) == 2:
        bin_image = image
    else:
        gimage = grey_scale(image)
        bin_image = gimage > 10
        #print bin_image, 'inside conditional'
    #print bin_image, 'outside conditional'
    return bin_image.astype(int)
        
def matches_exist(template, image, tolerance=1):
    # just taken from convolution def
    expected = numpy.count_nonzero(template)
    ih, iw = image.shape
    th, tw = template.shape

    # Pad image to even dimensions
    if ih % 2 or iw % 2:
        if ih % 2:
            ih += 1
        if iw % 2:
            iw += 1
        bin_image = pad_bin_image_to_shape(image, (ih, iw))
    if expected == 0:
        return []

    # Calculate the convolution of the FFT's of the image & template
    convolution_freqs = rfft2(image) * rfft2(template[::-1, ::-1],
                                                 image.shape)
    convolution_image = irfft2(convolution_freqs)
    found_bitmap = convolution_image > (expected - tolerance)
    if True in found_bitmap:
        return True
    else:
        return False
        
def compare_sizes(template, image, tolerance=0.1):
    ih, iw = image.shape
    th, tw = template.shape
    # take absolute value of the difference between the sizes
    height_difference = abs(ih-th)
    if height_difference < tolerance*ih or height_difference < tolerance*th:
        height_result = True
    else:
        height_result = False
    width_difference = abs(iw-tw)
    if width_difference < tolerance*iw or width_difference < tolerance*tw:
        width_result = True
    else:
        width_result = False
    return height_result, width_result
    
    
def is_similar(template, image, match_tolerance=1, size_tolerance=0.1):
    #print template, image
    bin_image, bin_template = binarise_image(image), binarise_image(template)
    #print bin_image, bin_template, 'binarised'
    if matches_exist(bin_template, bin_image, match_tolerance):
        #print "in conditional"
        height_compare, width_compare = compare_sizes(bin_template, bin_image, size_tolerance)
        if height_compare and width_compare:
            return True
        else:
            return "matches exist- size different"
    else:
        return False
    

def find_similar_in_repo(template, repo, match_tolerance=1, size_tolerance=0.1):
    # repo is a dictionary, so think we can just loop over keys
    # just save similar images, or ones with matches 
    similar = []
    matches_different_size = []
    no_match = []
    for key in repo:
        image = repo[key].image
        result = is_similar(template, image, match_tolerance=match_tolerance, size_tolerance=size_tolerance) 
        if result == True:
            similar.append(key)
        if result == "matches exist- size different":
            matches_different_size.append(key)
        elif result == False:
            no_match.append(key)
    return similar, matches_different_size, no_match

