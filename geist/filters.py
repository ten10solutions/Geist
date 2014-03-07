from itertools import islice


class LocationFinderFilter(object):
    def __init__(self, filter_func, finder):
        self.filter_func = filter_func
        self.finder = finder

    def find(self, gui):
        for loc in self.finder.find(gui):
            if self.filter_func(loc):
                yield loc

    def __repr__(self):
        return '(Filter results of %r with %r)' % (
            self.finder,
            self.filter_func
        )


class SortingFinder(object):
    """
    Sort found locations with the given key
    """
    def __init__(self, finder, key):
        self.finder = finder
        self.key = key

    def find(self, gui):
        for loc in sorted(self.finder.find(gui), key=self.key):
            yield loc

    def __repr__(self):
        return '<SortFinder %r with %r>' % (self.finder, self.key)


class SliceFinderFilter(object):
    """
    Slice the returned results
    """

    def __init__(self, finder, slice=None):
        if slice.start < 0 or slice.stop < 0 or slice.step <= 0:
            raise ValueError("Slices must be positive")
        self.finder = finder
        self.slice = slice

    def find(self, gui):
        if self.slice is None:
            for loc in self.finder.find(gui):
                yield loc
            return

        for loc in islice(self.finder.find(gui),
                          self.slice.start, self.slice.stop, self.slice.step):
            yield loc

    def __getitem__(self, key):
        if isinstance(key, slice):
            return SliceFinderFilter(self.finder, slice=key)
        return SliceFinderFilter(self.finder, slice=slice(key, key + 1))

    def __repr__(self):
        return "%r[%d:%d:%s]" % (self.finder,
                                 self.slice.start, self.slice.stop,
                                 self.slice.step)
