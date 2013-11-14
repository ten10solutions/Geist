from __future__ import division
import numpy
import os
import os.path
import glob

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
            return numpy.load(imgpath)
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
        return iter(os.path.split(i)[1].rsplit('.',1)[0] for i in
                      glob.glob(os.path.join(self.__directory,'*.npy')))


class TemplateFinderFromRepo(object):
    def __init__(self, repo, finder_constructor):
        self._repo = repo
        self._finder_constructor = finder_constructor

    def __dir__(self):
        return self._repo.entries

    def __getattr__(self, name):
        if name in self._repo:
            return self._finder_constructor(self._repo[name])
        else:
            raise NameError(name)
