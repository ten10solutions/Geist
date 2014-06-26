from __future__ import division
import numpy as np


class BaseFinder(object):
    """
    Base class for all finders.
    """

    def find(self, in_location):
        raise NotImplemented(
            "find should be implemented in the inherited class")


class Location(BaseFinder):
    def __init__(self, rel_x, rel_y, w=1, h=1, main_point_offset=None,
                 parent=None, image=None):
        """rel_x, rel_y, w, h are all cast to integers as its assumed we are
        dealing with whole pixels.
        """
        rel_x, rel_y, w, h = int(rel_x), int(rel_y), int(w), int(h)

        if rel_x < 0:
            raise ValueError('rel_x must be >= 0')
        if rel_y < 0:
            raise ValueError('rel_y must be >= 0')
        if w < 1:
            raise ValueError('w must be >= 1')
        if h < 1:
            raise ValueError('h must be >= 1')
        if parent is not None and rel_x + w > parent.w:
            raise ValueError('rel_x + w must be <= parent.w or parent must be None')
        if parent is not None and rel_y + h > parent.h:
            raise ValueError('rel_y + h must be <= parent.h or parent must be None')

        self._rel_x, self._rel_y, self._w, self._h = (
            int(rel_x),
            int(rel_y),
            int(w),
            int(h)
        )

        if main_point_offset is None:
            self._main_point_offset = (w // 2, h // 2)
        else:
            self._main_point_offset = tuple(int(i) for i in main_point_offset)
        self._parent = parent
        if image is not None:
            ih, iw = image.shape[:2]
            if ih != h or iw != w:
                raise AssertionError('image width and height should be the '
                                     'same as the locations')
        self._image = image

    @property
    def parent(self):
        return self._parent

    @property
    def image(self):
        if self.w < 1 or self.h < 1:
            raise AttributeError(
                "Can not get image from Locations with zero width or height"
            )
        if self.parent is not None:
            return self.parent.image[self.rel_y:self.rel_y + self.h,
                                     self.rel_x:self.rel_x + self.w]
        if self._image is not None:
            return self._image
        else:
            return np.zeros((self.h, self.w, 3), dtype=np.uint8)

    @property
    def rel_x(self):
        return self._rel_x

    @property
    def rel_y(self):
        return self._rel_y

    @property
    def x(self):
        if self.parent is None:
            return self.rel_x
        else:
            return self.rel_x + self.parent.x

    @property
    def y(self):
        if self.parent is None:
            return self.rel_y
        else:
            return self.rel_y + self.parent.y

    @property
    def w(self):
        return self._w

    @property
    def h(self):
        return self._h

    def find(self, in_location):
        if (
            self.rel_x + self.w <= in_location.x + in_location.w
        ) and (
            self.rel_y + self.h <= in_location.y + in_location.h
        ):
            yield self.copy(parent=in_location)

    def copy(self, **update_attrs):
        attrs = dict(
            (attr, getattr(self, attr)) for attr in
            ['rel_x', 'rel_y', 'w', 'h', 'main_point_offset', 'parent']
        )
        attrs['image'] = self._image
        attrs.update(update_attrs)
        return Location(**attrs)

    @property
    def main_point_offset(self):
        return self._main_point_offset

    @property
    def main_point(self):
        return (
            self.x + self._main_point_offset[0],
            self.y + self._main_point_offset[1]
        )

    @property
    def center(self):
        return (self.x + (self.w // 2), self.y + (self.h // 2))

    @property
    def rect(self):
        return (self.x, self.y, self.w, self.h)

    @property
    def area(self):
        return self.w * self.h

    def __repr__(self):
        return "Location(x=%r, y=%r, w=%r, h=%r, main_point_offset=%r, parent=%r)" % (
            self.x,
            self.y,
            self.w,
            self.h,
            self._main_point_offset,
            self.parent,
        )

    def equals_considering_only_image(self, other):
        return np.all(np.equal(self.image, other.image))

    def __eq__(self, other):
        if self.parent != other.parent:
            return False
        if ((self.rel_x, self.rel_y, self.w, self.h) !=
                (other.rel_x, other.rel_y, other.w, other.h)):
            return False
        if self.main_point_offset != other.main_point_offset:
            return False
        return True

    def __ne__(self, other):
        return not self.__eq__(other)


class LocationList(list, BaseFinder):
    def find(self, in_location):
        for loc in self:
            try:
                yield next(loc.find(in_location))
            except StopIteration:
                pass
