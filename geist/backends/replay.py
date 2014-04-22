from __future__ import division, absolute_import, print_function
import os
import json
import base64
import StringIO
import wrapt
from PIL import Image
from . import get_platform_backend
from ..core import GUI, Location, LocationList
from ._common import BackendActionBuilder
import numpy
import logging

logger = logging.getLogger(__name__)

"""These backends provide support for writing tests of code using Geist.

The intention is for you to write unit tests which can be run in record mode
on the system under test which will produce an output file which can then run
the test in playback mode.

Example:

    User the @geist_replay decorator on your test.

    To record set the GEIST_REPLAY_MODE=record environment variable

        Windows:
            set GEIST_REPLAY_MODE=record
        Linux:
            export GEIST_REPLAY_MODE=record

    To replay don't declare or set the GEIST_REPLAY_MODE to any other value.


"""


_MODE_ENV_VAR_NAME = 'GEIST_REPLAY_MODE'
_RECORD_MODE_ENV_VAR_VALUE = 'record'


@wrapt.decorator
def geist_replay(wrapped, instance, args, kwargs):
    """Wraps a test of other function and injects a Geist GUI which will
    enable replay (set environment variable GEIST_REPLAY_MODE to 'record' to
    active record mode."""
    name = wrapped.__name__
    filename = '%s.log' % (name,)
    if os.environ.get(_MODE_ENV_VAR_NAME, '') == _RECORD_MODE_ENV_VAR_VALUE:
        platform_backend = get_platform_backend()
        backend = RecordingBackend(
            source_backend=platform_backend,
            recording_filename=filename
        )
    else:
        backend = PlaybackBackend(
            recording_filename=filename
        )
    gui = GUI(backend)
    return wrapped(gui, *args, **kwargs)


class _ActionsTransaction(object):
    def __init__(self, backend):
        self._actions_builder = BackendActionBuilder(backend)

    def __enter__(self):
        return self._actions_builder

    def __exit__(self, *args):
        self._actions_builder.execute()
        return False


class PlaybackBackend(object):
    def __init__(self, recording_filename='backend_recording.log'):
        self._record_file = open(recording_filename, 'rb')

    def capture_locations(self):
        logger.debug('replay func: "capture_locations" called')
        try:
            data = json.loads(next(self._record_file))
        except StopIteration:
            raise AssertionError('capture_locations end of replay')
        if data['func'] != 'capture_locations':
            raise AssertionError(
                "function mismatch recorded %r != 'capture_locations'" %
                (data['func'],)
            )
        b64_locations = data['locations']
        location_list = LocationList()
        for b64_location in b64_locations:
            base64_png = b64_location['base64_png']
            string_file = StringIO.StringIO(
                base64.b64decode(base64_png)
            )
            x, y, w, h = (
                b64_location['x'],
                b64_location['y'],
                b64_location['w'],
                b64_location['h']
            )
            image = numpy.array(Image.open(string_file))
            location_list.append(Location(x, y, w, h, image=image))
        return location_list

    def actions_transaction(self):
        return _ActionsTransaction(self)

    def _json_type_coercian(self, data):
        return json.loads(json.dumps(data))

    def __getattr__(self, name):
        def func(*args, **kwargs):
            logger.debug('replay func: %r called with args: %r, kwargs %r', name, args, kwargs)
            try:
                data = json.loads(next(self._record_file))
            except StopIteration:
                raise AssertionError('%s end of replay' % (name,))
            func_name = name
            recd_name = data['func']
            if func_name != recd_name:
                raise AssertionError(
                    'function mismatch recorded %r != %r' %
                    (recd_name, func_name)
                )
            recd_args = data['args']
            recd_kwargs = data['kwargs']
            if self._json_type_coercian(args) != recd_args:
                raise AssertionError(
                    'args mismatch recorded %r != %r' % (recd_args, args)
                )
            if self._json_type_coercian(kwargs) != recd_kwargs:
                raise AssertionError(
                    'kwargs mismatch recorded %r != %r' % (recd_kwargs, kwargs)
                )
        return func


class RecordingBackend(object):
    def __init__(
        self,
        source_backend=None,
        recording_filename='backend_recording.log',
        **kwargs
    ):
        if source_backend is None:
            raise ValueError('source_backend is required for %r' % (self))
        self._source_backend = source_backend
        self._record_file = open(recording_filename, 'wb')

    def _write_action(self, funcname, *args, **kwargs):
        json.dump(
            {'func': funcname, 'args': args, 'kwargs': kwargs},
            self._record_file
        )
        self._record_file.write('\n')
        self._record_file.flush()

    def _write_capture_locations(self, locations):
        b64_locations = []
        for location in locations:
            string_file = StringIO.StringIO()
            Image.fromarray(location.image).save(string_file, 'png')
            b64_png = base64.b64encode(string_file.getvalue())
            b64_locations.append({
                'base64_png': b64_png,
                'x': location.x,
                'y': location.y,
                'w': location.w,
                'h': location.h
            })
        json.dump(
            {'func': 'capture_locations', 'locations': b64_locations},
            self._record_file
        )
        self._record_file.write('\n')
        self._record_file.flush()

    def capture_locations(self):
        locations = list(self._source_backend.capture_locations())
        self._write_capture_locations(locations)
        return locations

    def actions_transaction(self):
        return _ActionsTransaction(self)

    def __getattr__(self, name):
        if not name.startswith('_'):
            def callable_action(*args, **kwargs):
                getattr(self._source_backend, name)(*args, **kwargs)
                self._write_action(name, *args, **kwargs)
            return callable_action
