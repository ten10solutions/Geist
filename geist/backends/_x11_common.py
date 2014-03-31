from __future__ import division, absolute_import, print_function

from ooxcb.protocol import (
    xtest,
)
from ooxcb.constant import (
    ButtonPress,
    ButtonRelease,
    KeyPress,
    KeyRelease,
    MotionNotify
)
import ooxcb
from ooxcb.keysymdef import keysyms
import subprocess
import os
from ._common import BackendActionBuilder


xtest.mixin()


class _ActionsTransaction(object):
    def __init__(self, backend):
        self._conn = backend._conn
        self._actions_builder = BackendActionBuilder(backend)

    def __enter__(self):
        return self._actions_builder

    def __exit__(self, *args):
        #with self._conn.bunch():
        self._actions_builder.execute()
        return False


class GeistXBase(object):

    KEY_NAME_TO_CODE = keysyms
    KEY_NAME_TO_CODE_IGNORE_CASE = {name.lower(): value
                                    for name, value in keysyms.iteritems()}

    def __init__(self, **kwargs):
        display = kwargs.get('display', ':0')

        self._display = display
        self._conn = ooxcb.connect(display)
        self._root = self._conn.setup.roots[self._conn.pref_screen].root

    @property
    def display(self):
        return self._display

    def create_process(self, command):
        env = dict(os.environ)
        env['DISPLAY'] = self.display
        dev_null = open('/dev/null', 'w')
        return subprocess.Popen(
            command, shell=True, env=env, stdout=dev_null,
            stderr=subprocess.STDOUT
        )

    def actions_transaction(self):
        return _ActionsTransaction(self)

    def _get_key_code_from_name(self, name):
        if name == 'shift':
            symb = GeistXBase.KEY_NAME_TO_CODE['Shift_L']
        elif name in GeistXBase.KEY_NAME_TO_CODE:
            symb = GeistXBase.KEY_NAME_TO_CODE[name]
        elif name.lower() in GeistXBase.KEY_NAME_TO_CODE_IGNORE_CASE:
            symb = GeistXBase.KEY_NAME_TO_CODE_IGNORE_CASE[name]
        else:
            raise ValueError('unhandled key %r' % (name,))
        return self._conn.keysyms.get_keycode(symb)

    def key_down(self, name):
        key_code = self._get_key_code_from_name(name)
        with self._conn.bunch():
            self._conn.xtest.fake_input_checked(
                KeyPress,
                detail=key_code
            )

    def key_up(self, name):
        key_code = self._get_key_code_from_name(name)
        with self._conn.bunch():
            self._conn.xtest.fake_input_checked(
                KeyRelease,
                detail=key_code
            )

    def button_down(self, button_num):
        with self._conn.bunch():
            self._conn.xtest.fake_input_checked(
                ButtonPress,
                detail=button_num
            )

    def button_up(self, button_num):
        with self._conn.bunch():
            self._conn.xtest.fake_input_checked(
                ButtonRelease,
                detail=button_num
            )

    def move(self, point):
        x, y = point
        with self._conn.bunch():
            self._conn.xtest.fake_input_checked(
                MotionNotify,
                rootX=x,
                rootY=y,
            )

    def close(self):
        if hasattr(self, '_conn'):
            self._conn.disconnect()
            del self._conn

    def __del__(self):
        self.close()
