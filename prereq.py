try:
    get_ipython().magic(u'pylab')
except (NameError,):
    pass
from geist import (
    GUI,
    DirectoryRepo,
    ApproxTemplateFinder,
    ExactTemplateFinder,
    left_of,
    right_of,
    below,
    row_aligned,
    column_aligned,
    TemplateFinderFromRepo,
    LocationOperatorFinder,
    LocationFinderFilter,
    MultipleFinderFinder,
    BinaryRegionFinder,
    text_finder_filter_from_path,
    max_horizontal_separation,
    ThresholdTemplateFinder,
    ColourRegionFinder

)
from geist.backends.android import GeistAndroidBackend
from geist.vision import grey_scale
from geist.colour import rgb_to_hsv, hsv
from geist.keyboard import KeyUp, KeyDown, KeyDownUp
from PIL import Image
from scipy.ndimage import binary_erosion, binary_dilation
from geist.pyplot import Viewer

repo = DirectoryRepo('test_repo')
backend = GeistAndroidBackend()
gui = GUI(backend)
V = Viewer(gui, repo)
S = V.save
C = V.show_capture
F = V.show_found
R = V.show_repo

top = lambda locations: sorted(locations, key=lambda loc: loc.y)[0]
bottom = lambda locations: sorted(locations, key=lambda loc: loc.y)[-1]
left = lambda locations: sorted(locations, key=lambda loc: loc.x)[0]
right = lambda locations: sorted(locations, key=lambda loc: loc.x)[-1]

approx_finder = TemplateFinderFromRepo(repo, ApproxTemplateFinder)
exact_finder = TemplateFinderFromRepo(repo, ExactTemplateFinder)
