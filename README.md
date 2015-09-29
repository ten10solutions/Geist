Geist
=====

[![Build Status](https://travis-ci.org/thetestpeople/Geist.svg?branch=master)](https://travis-ci.org/thetestpeople/Geist)

Computer vision based UI automation library.

Please file bug reports.

Repository
========== 

Folder to serve as a location for saved images. These images take the form of
an npy file, a numpy array. These can be used to search for the image within the
display.

Example:

``` python
from geist import DirectoryRepo

repo = DirectoryRepo('root_folder/folder/geist_repo')
```

Backends
========

A backend is how geist interacts with the screen. This is different depending on
which operating system geist is being run from. This is called with the argument
of a screen number. For example, Xvfb based backends on linux can be passed the 
number 2 to start the Xvfb backend on screen number 2.

Example:

``` python
from geist.backends import get_platform_backend

backend = get_platform_backend(screen_number)
```

GUI
===

The gui is the user interface that geist will begin watching on. This contains 
a number of properties/methods used to interact with the screen. It is 
initialised with a backend.

Example:

``` python
from geist import GUI

gui = GUI(backend)
```

Viewer
======

A viewer is used to display an image of what geist is looking at at any one time, as well as some
functionality to interactively extract and save image data. It is initialised with a gui and a
repository. This is done for you in the prereq.py file.

Example:

``` python
from geist.pyplot import Viewer

viewer = Viewer(gui, repository)
```

The first useful method a viewer provides is the ability to view what is happening on the gui with
show_capture. You can zoom in to a particular part of the image using the magnifying glass button
and return the the original view with the home button.

Example:

``` python
viewer.show_capture()
```

You can also save the image that is displayed in the viewer to the repository, which can then be
used later to build finders. To call the save method, pass in the name you want to save the image
as. If an image with that name exists already you'll need to pass the set force to True.

Example:

``` python
viewer.save('image_name')
viewer.save('image_name', force =True)
```

You can view the results of a particular finder with the show_found function. This will highlight
any part of the gui which the finder matches, whether it is one result or many. It is called with
the finder as an argument.

Example:

``` python
viewer.show_found(finder)
```

You can view any images that you have previously saved by calling the show_repo method and
passing in the name of the captured image as a string.

You can get the colour of the image in the viewer by using the get_colour method. This will return
a hsv object which can be used to create finders, as well as printing out the values. If there is
just one colour in this image, it will match only this colour. If there are multiple colours, it
will match a range where h is between the minimum h value and maximum h value with the same
being true for s and v.

Example:

``` python
colour = viewer.get_colour()
```

Some additional information on Geist can be found [here] (https://github.com/thetestpeople/Geist).

Creating Geist Finders
----------------

Geist locates things based on finders. A finder will either return a Location object, or a collection of
location objects. A location object is an area of the screen. It has an image attribute as well as
an x and y position on the screen in pixels. It also has h and w attribute which are it's size in 
pixels.

There are also filters available to filter down a list of found Locations as well as a way to slice into
the collection to get a subset, usually done by ordering the collection by some property.

There are common examples below.

### Finding Saved Images

Saved images are found using either exact finders or finders based on a threshold. Finders based on
a threshold will find things with a degree of similarity. There is a predefined threshold finder with
a reasonable threshold set. They are created as follows, taking a repo to pull images from:

``` python
approx_finder = TemplateFinderFromRepo(repo, ApproxTemplateFinder)
exact_finder = TemplateFinderFromRepo(repo, ExactTemplateFinder)
threshold_finder = TemplateFinderFromRepo(
    repo,
    lambda template: ThresholdTemplateFinder(template, threshold_integer)
    )
```

A saved image can be retrieved and used as a finder with the following syntax:

```python
# This example uses a viewer,show_found to show the finder in a window. During an actual
# script you are more like to use one of the methods on a gui object such as gui.find_all
# or gui.wait_find_one
viewer.show_found(approx_finder.saved_image_name)
```

### Finding By Colour

You can search for regions of a certain colour by defining a colour or range of colours. There are
predefined colours in geist.colour or you can define your own using the hsv function from
geist.colour. We then locate a region with that colour using a BinaryRegionFinder. Example below:

```python
from geist import BinaryRegionFinder
from geist.colour import hsv

# Colours are defined based on their hue, saturation and value. There are conditions for
# upper and lower bounds for each of the h,s and v arguments in this example but you could
# just as easily swap out '(h >= 160) & (h <= 165)' for '(h == 162)' for a specific value.
PALE_BLUE = hsv(lambda h, s, v: (
    (h >= 160) &
    (h <= 165) &
    (s >= 82) &
    (s <= 87) &
    (v > 250)&
    (v <= 255)))

viewer.show_found(BinaryRegionFinder(PALE_BLUE))
```

### Finding Based on Position

Sometimes we want to find things based on their position on the screen. Geist has a number of built
in functions such as bottom_most, column_aligned, intersects etc. These can be imported from geist.
Some of them which require two finders such as column_aligned or intersects need to be wrapped in
a LocationOperatorFinder which also comes from geist.

```python
from geist import (
    LocationOperatorFinder,
    right_most,
    row_aligned,
)

viewer.show_found(right_most(BinaryRegionFinder(PALE_BLUE)))

# Find the saved image that has the same vertical alignment as a blue thing.
viewer.show_found(LocationOperatorFinder(
    approx_finder.saved_image_name,
    row_aligned,
    BinaryRegionFinder(PALE_BLUE)
    ))
```

### Filtering, Sorting and Slicing

Sometimes you want to filter down the amount of results that you've got. For example, we can
imagine that our pale blue finder might find a lot of things. We can filter them by the attributes
of the Location objects using the LocationFinderFilter. Example below:

```python
from geist import LocationfinderFilter

# Find only the pale blue things with a height between 15 and 25 pixels
viewer.show_found(LocationFinderFilter(
    lambda loc: 15 < loc.h < 25,
    BinaryRegionFinder(PALE_BLUE)))
```

Sometimes we want to take a slice of something, such as only the first one or the 2nd to the 5th.
We do this using a SliceFinderFilter. Usually when taking a slice, we would want to order them 
using the SortingFinder first. for example we may want to order them based on width and find
only the largest result. Example below.

```python
from geist import (
    SliceFinderFilter,
    SortingFinder,
)

# Sorted based on smallest to largest height.
sorted_blue_things_small = SortingFinder(BinaryRegionFinder(PALE_BLUE), lambda loc: loc.h)

# Sorted based on largest to smallest width, reverse=True flips the sort order
sorted_blue_things_large = SortingFinder(
    BinaryRegionFinder(PALE_BLUE),
    lambda loc: loc.w,
    reverse=True
)

# Blue thing with the smallest height
viewer.show_found(SliceFinderFilter(sorted_blue_things_small)[0])

# Blue things with width that are 2nd-5th largest of the overall result set.
viewer.show_found(SliceFinderFilter(sorted_blue_things_large)[1:4])
```
