from geist.backends.windows import get_all_windows




coldharbour_window_finder = LocationFinderFilter(
    lambda loc: loc.window.title.startswith(u'HOMECARE Domiciliary Care'),
    WindowFinder()
    )


class _WindowLocation(Location):
    """
        Adds window to Location object
    """
    def __init__(self, window, parent):
         self.window = window
        Location.__init__(self, 1, 1, 10, 10, parent=parent)


class WindowFinder(BaseFinder):
    """
        Finds all windows in the given location
    """
    def find(self, in_location):
        for window in get_all_windows():
            try:
                yield _WindowLocation(window, in_location)
            except ValueError:
                 pass



class WindowTitleFinder(BaseFinder):
    """
        Creates a Finder which finds Windows with a particular title
    """
    def __init__(self, title):
        self.finder = LocationFinderFilter(
           lambda loc: (title in loc.window.title),
            WindowFinder()
            )


class WindowTitleClassnameFinder(BaseFinder):
    """
        Creates a Finder which finds Windows with a particular title
    """
    def __init__(self, title, classname):
        self.finder = LocationFinderFilter(
           lambda loc: (title in loc.window.title
           and classname == loc.window.classname),
            WindowFinder()
            )
