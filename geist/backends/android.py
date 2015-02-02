from __future__ import division, absolute_import, print_function

import androidwebui.device_store as device_store
import androidwebui.actions as actions
import logging
import numpy as np
import struct
import subprocess
import zlib
from ..finders import Location, LocationList
from ._common import BackendActionBuilder

logger = logging.getLogger(__name__)


class _ActionsTransaction(object):
    def __init__(self, backend):
        self._actions_builder = BackendActionBuilder(backend)

    def __enter__(self):
        return self._actions_builder

    def __exit__(self, *args):
        self._actions_builder.execute()
        return False


class AndroidToNumpyReader(object):
    _HEADER = struct.Struct('III')

    def __init__(self, fb, decompress=False):
        self.h = 0
        self.w = 0
        if decompress:
            wbits = zlib.MAX_WBITS | 16
            self._fb = zlib.decompress(fb, wbits)
        else:
            self._fb = fb
        self._np = self._read_dump()
        self._read_w_h_from_header()

    def _read_dump(self):
        return np.fromstring(self._fb, np.uint8)

    def _read_w_h_from_header(self):
        self.w, self.h = AndroidToNumpyReader._HEADER.unpack_from(self._np)[:2]
        logger.debug('read header, w:%s, h%s' % (self.w, self.h))

    def get_rect(self):
        return 0, 0, self.w, self.h

    def get_image(self):
        return self._np[12:].reshape((self.h, self.w, 4))[:, :, :3]


class GeistAndroidBackend(object):
    def __init__(self, **kwargs):
        self.device_id = kwargs.get('device_id', None)
        logger.debug('New android backend with device %s' % self.device_id)
        self._devices = device_store.DevicesStore()
        self._devices.update()
        logger.debug('%d devices found' % len(self._devices.get_all_devices()))

    def get_device(self, device_id=None):
        if device_id:
            device = self._devices.get_by_device_id(device_id)
        elif self.device_id:
            device = self._devices.get_by_device_id(self.device_id)
        else:
            device = self._devices.get_first_device()
        return device if device else None

    def actions_transaction(self):
        return _ActionsTransaction(self)

    def capture_locations(self, device_id=None):
        _stream = self.do_screencap(device_id)
        if not _stream:
            logger.warning('no device found')
        # use stream/buffer when we go back to actions.image
        # _buffer = ''.join(list(_stream))
        # _image = AndroidToNumpyReader(_buffer, True).get_image()
        _image = AndroidToNumpyReader(_stream, True).get_image()

        h, w = _image.shape[:2]
        return LocationList([Location(0, 0, w, h, image=_image)])

    def do_screencap(self, device_id=None, quality=1):
        device = self.get_device(device_id)
        if not device:
            return None
        # actions.image returns fbcompressed image, just use raw image for now
        # return actions.image(device, quality)
        process = subprocess.Popen(
            r'adb -s {adb_id} shell "screencap | gzip -1" | sed "s/\r$//"'.format(
                adb_id=device.adb_id
            ),
            shell=True,
            stdout=subprocess.PIPE
        )
        return process.stdout.read()

    def click(self, px, py, device_id=None):
        device = self.get_device(device_id)
        if not device:
            return None
        return actions.clickimage(device, px, py)

    def swipe(self, json_data, device_id=None, time=None):
        device = self.get_device(device_id)
        if not device:
            return None
        return actions.swipeimage(device, json_data, time)

    def press_button(self, button, device_id=None):
        device = self.get_device(device_id)
        if not device:
            return None
        return actions.button(device, button)

    def getrotation(self, device_id=None):
        device = self.get_device(device_id)
        if not device:
            return None
        return actions.getrotation(device)

    def button_down(self, button_num):
        pass

    def button_up(self, button_num):
        pass

    def move(self, point):
        x, y = point
        self.click(x, y)

    def close(self):
        pass

    def __del__(self):
        self.close()
