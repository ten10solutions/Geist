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
import json


def go_home():
    max_presses = 50
    while max_presses and not gui.find_all(approx_finder.centrescreen):
        backend.press_button("home")
        max_presses -= 1


def write_geist():
    backend.swipe(json.dumps(left_swipe))
    backend.swipe(json.dumps(left_swipe))
    gui.click(approx_finder.drawingapp)
    backend.click(660, 50)
    backend.swipe(json.dumps(geist_text))
    backend.click(560, 50)

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
    {"startx": 100, "starty": 1100, "endx": 700, "endy": 1100},
]
right_swipe = [
    {"startx": 700, "starty": 1100, "endx": 100, "endy": 1100},
]

geist_text = [
    {"startx": 268, "starty": 476, "endx": 266, "endy": 474},
    {"startx": 178, "starty": 344, "endx": 170, "endy": 308},
    {"startx": 172, "starty": 306, "endx": 138, "endy": 282},
    {"startx": 124, "starty": 282, "endx": 66, "endy": 302},
    {"startx": 62, "starty": 304, "endx": 68, "endy": 380},
    {"startx": 62, "starty": 376, "endx": 56, "endy": 470},
    {"startx": 58, "starty": 472, "endx": 110, "endy": 564},
    {"startx": 110, "starty": 564, "endx": 142, "endy": 556},
    {"startx": 148, "starty": 556, "endx": 180, "endy": 550},
    {"startx": 180, "starty": 550, "endx": 178, "endy": 492},
    {"startx": 180, "starty": 490, "endx": 176, "endy": 460},
    {"startx": 180, "starty": 452, "endx": 132, "endy": 466},
    {"startx": 234, "starty": 502, "endx": 278, "endy": 490},
    {"startx": 280, "starty": 488, "endx": 266, "endy": 456},
    {"startx": 262, "starty": 456, "endx": 242, "endy": 448},
    {"startx": 240, "starty": 446, "endx": 222, "endy": 474},
    {"startx": 220, "starty": 476, "endx": 260, "endy": 542},
    {"startx": 260, "starty": 536, "endx": 290, "endy": 524},
    {"startx": 324, "starty": 442, "endx": 330, "endy": 548},
    {"startx": 308, "starty": 376, "endx": 308, "endy": 376},
    {"startx": 406, "starty": 454, "endx": 394, "endy": 436},
    {"startx": 388, "starty": 432, "endx": 352, "endy": 444},
    {"startx": 350, "starty": 442, "endx": 368, "endy": 502},
    {"startx": 370, "starty": 494, "endx": 404, "endy": 492},
    {"startx": 406, "starty": 494, "endx": 406, "endy": 530},
    {"startx": 404, "starty": 534, "endx": 372, "endy": 546},
    {"startx": 366, "starty": 546, "endx": 346, "endy": 520},
    {"startx": 460, "starty": 238, "endx": 476, "endy": 594},
    {"startx": 412, "starty": 346, "endx": 490, "endy": 322},
]
