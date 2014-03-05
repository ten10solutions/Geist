from __future__ import division, absolute_import, print_function

from .visualfinders import (
    ApproxTemplateFinder,
    ExactTemplateFinder,
    ThresholdTemplateFinder,
    ColourRegionFinder,
    BinaryRegionFinder,
    MultipleFinderFinder,
    GreyscaleRegionFinder,
    text_finder_filter_from_path,
    TextFinderFilter,
)

from .layoutfinders import (
    LocationOperatorFinder,
    MergeLocationsFinderFilter,
    max_horizontal_separation,
    max_vertical_separation,
    above,
    below,
    right_of,
    left_of,
    column_aligned,
    row_aligned,
    intersects,
)

from .repo import (
    DirectoryRepo,
    TemplateFinderFromRepo,
)

from .core import (
    Location,
    NotFoundError,
    GUI,
    FileGUI,
    GUICaptureFilter,
    LocationList,
    LocationFinderFilter
)
from .backends import get_platform_backend

__all__ = [
    "ApproxTemplateFinder",
    "ExactTemplateFinder",
    "ThresholdTemplateFinder",
    "ColourRegionFinder",
    "BinaryRegionFinder",
    "MultipleFinderFinder",
    "GreyscaleRegionFinder",
    "text_finder_filter_from_path",
    "TextFinderFilter",
    "LocationOperatorFinder",
    "MergeLocationsFinderFilter",
    "max_horizontal_separation",
    "max_vertical_separation",
    "above",
    "below",
    "right_of",
    "left_of",
    "column_aligned",
    "row_aligned",
    "intersects",
    "DirectoryRepo",
    "TemplateFinderFromRepo",
    "Location",
    "NotFoundError",
    "GUI",
    "FileGUI",
    "GUICaptureFilter",
    "LocationList",
    "LocationFinderFilter"
]
