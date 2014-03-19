import time
from . import logger


class _DesciptiveCallable(object):
    def __init__(self, doc, func):
        self.doc = doc
        self.func = func

    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)

    def __str__(self):
        return self.doc


class BackendActionBuilder(object):
    def __init__(self, backend):
        self._backend = backend
        self._actions = []

    def add_button_down(self, button):
        self._actions.append(
            _DesciptiveCallable(
                "button down %r" % (button,),
                lambda: self._backend.button_down(button)
            )
        )

    def add_button_up(self, button):
        self._actions.append(
            _DesciptiveCallable(
                "button up %r" % (button,),
                lambda: self._backend.button_up(button)
            )
        )

    def add_key_down(self, key_name):
        self._actions.append(
            _DesciptiveCallable(
                "key down %r" % (key_name,),
                lambda: self._backend.key_down(key_name)
            )
        )

    def add_key_up(self, key_name):
        self._actions.append(
            _DesciptiveCallable(
                "key up %r" % (key_name,),
                lambda: self._backend.key_up(key_name)
            )
        )

    def add_move(self, point):
        self._actions.append(
            _DesciptiveCallable(
                "move %r" % (point,),
                lambda: self._backend.move(point)
            )
        )

    def add_wait(self, seconds):
        self._actions.append(
            _DesciptiveCallable(
                "wait %r seconds" % (seconds,),
                lambda: time.sleep(seconds)
            )
        )

    def execute(self):
        for action in self._actions:
            logger.debug(action)
            action()
