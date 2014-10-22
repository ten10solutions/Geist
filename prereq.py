try:
    get_ipython().magic(u'pylab')
except (NameError,):
    pass
from geist import (
    GUI,
    DirectoryRepo,
    ApproxTemplateFinder,
    ExactTemplateFinder,
    TemplateFinderFromRepo,
)
from geist.backends.android import GeistAndroidBackend
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

left_swipe = [
    {"startx": 100, "starty": 500, "endx": 700, "endy": 500},
]
right_swipe = [
    {"startx": 700, "starty": 500, "endx": 100, "endy": 500},
]
