import numpy as np


def find_potential_match_regions(template, transformed_array, method='correlation', raw_tolerance=0.666):
    """To prevent prohibitively slow calculation of normalisation coefficient at each point in image
       find potential match points, and normalise these only these.
       This function uses the definitions of the matching functions to calculate the expected match value
       and finds positions in the transformed array matching these- normalisation will then eliminate false positives
    """
    if method == 'correlation':
        match_value  = np.sum(template**2) # this will be the value of the match in the
    elif method == 'squared difference':
        match_value = 0
    elif method == 'correlation coefficient':
        temp_minus_mean = template - np.mean(template)
        match_value = np.sum(temp_minus_mean**2)
    else:
        raise ValueError('Matching method not implemented')
    condition = ((np.round(transformed_array, decimals=3)>=match_value*raw_tolerance) &
                 (np.round(transformed_array, decimals=3)<=match_value*(1./raw_tolerance)))
    return np.transpose(condition.nonzero())# trsnposition and omparison above take most time




# correlation coefficient matches at top left- perfect for tiling
# correlation matches to bottom right- so requires transformation for tiling
def get_tiles_at_potential_match_regions(image, template, transformed_array, method='correlation', raw_tolerance=0.001):
    if method not in ['correlation', 'correlation coefficient', 'squared difference']:
        raise ValueError('Matching method not implemented')
    h, w = template.shape
    match_points = find_potential_match_regions(template, transformed_array, method=method, raw_tolerance=raw_tolerance)
    match_points = [(match[0], match[1]) for match in match_points]
    # create tile for each match point- use dict so we know which match point it applies to
    # match point here is position of top left pixel of tile
    image_tiles_dict = {match_points[i]:image[match_points[i][0]:match_points[i][0]+h,match_points[i][1]:match_points[i][1]+w] for i in range(len(match_points))}
    return image_tiles_dict



###############################################

# image tiles dict is of form match_point coord:tile at that point
def normalise_correlation(image_tile_dict, transformed_array, template, normed_tolerance=1):
    """Calculates the normalisation coefficients of potential match positions
       Then normalises the correlation at these positions, and returns them
       if they do indeed constitute a match
    """
    template_norm = np.linalg.norm(template)
    image_norms = {(x,y):np.linalg.norm(image_tile_dict[(x,y)])*template_norm for (x,y) in image_tile_dict.keys()}
    match_points = image_tile_dict.keys()
    # for correlation, then need to transofrm back to get correct value for division
    h, w = template.shape
    #points_from_transformed_array = [(match[0] + h - 1, match[1] + w - 1) for match in match_points]
    image_matches_normalised = {match_points[i]:transformed_array[match_points[i][0], match_points[i][1]]/image_norms[match_points[i]] for i in range(len(match_points))}
    result = {key:value for key, value in image_matches_normalised.items() if np.round(value, decimals=3) >= normed_tolerance}
    return result.keys()


# image tiles dict is of form match_point coord:tile at that point
def normalise_correlation_coefficient(image_tile_dict, transformed_array, template, normed_tolerance=1):
    """As above, but for when the correlation coefficient matching method is used
    """
    template_mean = np.mean(template)
    template_minus_mean = template - template_mean
    template_norm = np.linalg.norm(template_minus_mean)
    image_norms = {(x,y):np.linalg.norm(image_tile_dict[(x,y)]- np.mean(image_tile_dict[(x,y)]))*template_norm for (x,y) in image_tile_dict.keys()}
    match_points = image_tile_dict.keys()
    # for correlation, then need to transofrm back to get correct value for division
    h, w = template.shape
    image_matches_normalised = {match_points[i]:transformed_array[match_points[i][0], match_points[i][1]]/image_norms[match_points[i]] for i in range(len(match_points))}
    normalised_matches = {key:value for key, value in image_matches_normalised.items() if np.round(value, decimals=3) >= normed_tolerance}
    return normalised_matches.keys()


