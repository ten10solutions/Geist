from __future__ import division
import numpy
import os
import os.path
import glob


class Template(object):
    def __init__(self, image, name, repo):
        self.image = image
        self.name = name
        self.repo = repo

    def __repr__(self):
        return "template %r in repo %r" % (self.name, self.repo)


class DirectoryRepo(object):
    def __init__(self, directory):
        self.__directory = os.path.abspath(directory)
        self.__ensure_dir_exists()

    def __ensure_dir_exists(self):
        try:
            os.makedirs(self.__directory)
        except:
            pass

    def __getitem__(self, key):
        self.__ensure_dir_exists()
        imgpath = os.path.join(self.__directory, key + '.npy')
        if os.path.exists(imgpath):
            return Template(numpy.load(imgpath), name=key, repo=self)
        else:
            raise KeyError(key)

    def __setitem__(self, key, value):
        self.__ensure_dir_exists()
        if type(value) is numpy.ndarray:
            numpy.save(os.path.join(self.__directory, key + '.npy'), value)
        else:
            raise ValueError('type not supported: %s' % (type(value),))

    def __delitem__(self, key):
        self.__ensure_dir_exists()
        imgpath = os.path.join(self.__directory, key + '.npy')
        if os.path.exists(imgpath):
            os.remove(imgpath)
        else:
            raise KeyError(key)

    @property
    def entries(self):
        return list(self)

    def __iter__(self):
        return iter(os.path.split(i)[1].rsplit('.', 1)[0] for i in
                    glob.glob(os.path.join(self.__directory, '*.npy')))

    def __repr__(self):
        return "directory repo %r" % (self.__directory, )


class TemplateBasedFinder(object):
    def __init__(self, repo, name, finder_constructor):
        self._name = name
        self._repo = repo
        self._finder_constructor = finder_constructor

    def find(self, in_location):
        for loc in self._finder_constructor(self._repo[self._name]).find(
            in_location
        ):
            yield loc

    def __repr__(self):
        return "%s finder for %r" % (self._finder_constructor, self._name)


class TemplateFinderFromRepo(object):
    def __init__(self, repo, finder_constructor):
        self._repo = repo
        self._finder_constructor = finder_constructor

    def __dir__(self):
        return self._repo.entries

    def __getattr__(self, name):
        return TemplateBasedFinder(self._repo, name, self._finder_constructor)
