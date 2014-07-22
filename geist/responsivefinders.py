from geist.finders import BaseFinder, Location
import time

class ClickingFinder(BaseFinder):
    """
        Clicks the item found, then returns its location
    """
    def __init__(self, finder, gui, **opts):
        self.gui = gui
        self.finder = finder
        self.opts = opts

    def find(self, in_location):
        self.gui.move(Location(0,0), **self.opts)
        for loc in self.finder.find(in_location):
            self.gui.click(Location(*loc.main_point), **self.opts)
            yield loc


class LocationChangeFinder(BaseFinder):
    """
        Initialise with a location, if the location image changes within
        the timeout, it returns the location
    """
    def __init__(self, location):
        self.location = location

    def find(self, in_location):
        new_location = next(self.location.find(in_location))
        if not self.location.equals_considering_only_image(new_location):
            yield new_location


class StopChangingFinder(BaseFinder):
    """
        Initialise with a location, and wait for the image in that location
        to stop
    """
    def __init__(self, location, period=10):
        self.current_location = location
        self.period = period
        self.stop_time = time.time() + self.period

    def find(self, in_location):
        if self.stop_time is None:
            self.stop_time = time.time() + self.period
        new_location = next(self.current_location.find(in_location))
        if self.current_location.equals_considering_only_image(new_location):
            if time.time() > self.stop_time:
                yield new_location
        else:
            self.current_location = new_location
            self.stop_time = time.time() + self.period
