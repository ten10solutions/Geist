"""
Run this script with ipython -i prereq.py
This starts ipython in interactive mode.

Use the viewer object to capture images and test finders in an interactive ipython
"""

try:
    get_ipython().magic(u'pylab')
except (NameError,):
    pass

from geist.backends import get_platform_backend

from geist import (
    GUI,
    DirectoryRepo,
)

from geist.pyplot import Viewer

# Mark the directory listed as the current image repository
repo = DirectoryRepo("C:\some_filepath") # <--------------- EDIT ME!!!!!!!!!!!!!!!

# Start a Geist backend, takes an optional screen number to capture.
backend = get_platform_backend()

# Start a Geist GUI
gui = GUI(backend)

# Viewer  object can be used to display results in image form
viewer = Viewer(login_page.gui, login_page.repo)
