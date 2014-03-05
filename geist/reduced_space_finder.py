def apply_hw_restrictions(image, dict):
        hmin, hmax, wmin, wmax = 0, image.shape[0], 0, image.shape[1]
        if 'h' in dict.keys():
            if '<' in dict['h'].keys():
                hmax = dict['h']['<']
            if '>' in dict['h'].keys():
                hmin = dict['h']['>']
        if 'w' in dict.keys():
            if '<' in dict['w'].keys():
                wmax = dict['w']['<']
            if '>' in dict['w'].keys():
                wmin = dict['w']['>']   
        return wmin, wmax, hmin, hmax

# example usage:
#approx_finder = TemplateFinderFromRepo(repo, ApproxTemplateFinder)
#test_dict = {'y':{'<': 800, '>': 600}}
#simulate_finder = ReducedSpatialFilter(test_dict, approx_finder.simulate)
class ReducedSpatialFilter(object):
    def __init__(self, dict, finder):
        self.dict = dict
        self.finder = finder
    
    def find(self, gui):
        x_add, y_add = 0, 0
        image = gui.capture()
        if 'x' in self.dict.keys():
              # chop off top if needed
            if '<' in self.dict['x'].keys():
                image = image[::, :self.dict['x']['<']]
            if '>' in self.dict['x'].keys():
                image = image[::,self.dict['x']['>']:]
                x_add = self.dict['x']['>']
        if 'y' in self.dict.keys():
              # chop off top if needed
            if '<' in self.dict['y'].keys():
                image = image[:self.dict['y']['<'], ::]
            if '>' in self.dict['y'].keys():
                image = image[self.dict['y']['>']:, ::]
                y_add = self.dict['y']['>']
        # tried removing yield but this means we return none
        results = self.finder.find_reduced(gui, image, y_add, x_add)
        # now filter by size, first work out what 
        hmin, hmax, wmin, wmax = apply_hw_restrictions(image, self.dict)
        for location in results:
            if hmin < location.h < hmax and wmin < location.w < wmax:
                yield location

        
    # so that things from here can be used in the operator finder below, need a find reduced function here
    def find_reduced(self, gui, image, y_add, x_add): 
        results = self.finder.find_reduced(gui, image, y_add, x_add)
        hmin, hmax, wmin, wmax = apply_hw_restrictions(image, self.dict)
        for location in results:
            if hmin < location.h < hmax and wmin < location.w < wmax:
                yield location
        


# a finder is thing we eventually look for, b finder is thing we first look for, and constrain a by b location and operator
# can't reuse existing 'below' etc as this compares 2 locations. 

def below_rel(loc):
    return {'y' : {'>': loc.h + loc.y}}

def above_rel(loc):
    return {'y': {'<': loc.y}}

def right_rel(loc):
    return {'x': {'>': loc.x + loc.w}}

def left_rel(loc):
    return {'x': {'<': loc.x}}
    
def all(loc):
    return {}

def each(loc):
    return loc
    
def null_operation(something, something_else):
    return True 
    
def column_aligned(loc):
    return {'x': {'>': loc.x + loc.w, '<': loc.x}}
    
def row_aligned(loc):
    return {'y': {'>': loc.y + loc.h, '<': loc.y}}

# position is x and y constraints, operator is w/h constraints and identical to previous
# position is where, relative to b, we should look
# operator is relation between b and a which must hold 
# example usage:
# table_dict = {'x': {'<': 600, '>': 0}, 'y':{'<': 300, '>': 90}, 'h':{'<': 30, '>': 5}, 'w':{'<': 100, '>': 5}}
# not really ideal as finds each 
#table_finder = ReducedSpatialFilter(
#        table_dict,
#        BinaryRegionFinder(
 #       lambda image: binary_erosion(grey_scale(image) > 100)))
        
        
#header5_column_finder = ReducedOperatorFinder(
#    table_finder,
#    approx_finder.header_5,
#    operator = column_aligned
#)
class ReducedOperatorFinder(object):
    def __init__(self, a_finder, b_finder, position='all', operator=null_operation):
        self.a_finder = a_finder
        self.b_finder = b_finder
        # specifies, for possible positions, how to turn that into a constraint
        self.dict_1 = {'left': left_rel, 'right': right_rel, 'below': below_rel, 'above': above_rel, 'all': all, 'column_aligned': column_aligned, 'row_aligned': row_aligned}
        # if multiple items found, which one to make comparison with
        self.dict_2 = {'left': left, 'right': right, 'below': bottom, 'above': top, 'all': each}
        self.position = self.dict_1[position]
        self.loc_choice = self.dict_2[position]
        self.operator = operator 
    
    def find(self, gui):
        b_locations = list(self.b_finder.find(gui))
        image = gui.capture()
        x_add, y_add = 0, 0
        # if we have multiple locations, take left most etc, using stuff defined in prereq
        #left_b, right_b, top_b, bottom_b = left(b_locations), right(b_locations), top(b_locations), bottom(b_locations)
        # argh i think this way we have no choice but to have a predefined set of operations
        contraints = self.position(self.loc_choice(b_locations))
        if 'x' in contraints.keys():
              # chop off top if needed
            if '<' in contraints['x'].keys():
                image = image[::, :contraints['x']['<']]
            if '>' in contraints['x'].keys():
                image = image[::,contraints['x']['>']:]
                x_add = contraints['x']['>']
        if 'y' in contraints.keys():
              # chop off top if needed
            if '<' in contraints['y'].keys():
                image = image[:contraints['y']['<'], ::]
            if '>' in contraints['y'].keys():
                image = image[contraints['y']['>']:, ::]
                y_add = contraints['y']['>']
        if type(self.a_finder) == ReducedOperatorFinder:
            results = self.a_finder.find(gui) 
        else:
            results = self.a_finder.find_reduced(gui, image, y_add, x_add)
        # think we need to check that b is contained in a region too
        for result in results:
            # print result - shows loads more than found when use those alone
            # can't convert Location into list
            for b_location in b_locations:
                if self.operator(result, b_location):
                    yield result


