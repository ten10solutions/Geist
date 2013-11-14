import time


class BackendActionBuilder(object):
    def __init__(self, backend):
        self._backend = backend
        self._actions = []

    def add_button_down(self, button):
        self._actions.append(lambda: self._backend.button_down(button))

    def add_button_up(self, button):
        self._actions.append(lambda: self._backend.button_up(button))

    def add_key_down(self, key_name):
        self._actions.append(lambda: self._backend.key_down(key_name))

    def add_key_up(self, key_name):
        self._actions.append(lambda: self._backend.key_up(key_name))

    def add_move(self, point):
        self._actions.append(lambda: self._backend.move(point))

    def add_wait(self, seconds):
        self._actions.append(lambda: time.sleep(seconds))

    def execute(self):
        for action in self._actions:
            action()
