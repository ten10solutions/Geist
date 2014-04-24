from __future__ import division, absolute_import, print_function
import os
import unittest
from geist import Location, GUI
from geist.backends.fake import GeistFakeBackend
from geist.backends.replay import (
    RecordingBackend,
    PlaybackBackend,
    geist_replay,
    _RECORD_MODE_ENV_VAR_VALUE,
)
_DIR = os.path.split(os.path.abspath(__file__))[0]


class EnvironmentContext(object):
    def __init__(self, **env):
        self._env = env

    def __enter__(self):
        self._old_env = dict((k, os.environ[k]) for k in self._env.keys()
                             if k in os.environ)
        os.environ.update(self._env)

    def __exit__(self, *args, **kwargs):
        os.environ.update(self._old_env)
        return False


class TestReplay(unittest.TestCase):
    def test_replay_capture_works(self):
        capture_file = os.path.join(
            _DIR,
            'test_replay_capture_works.log')
        backend = RecordingBackend(
            source_backend=GeistFakeBackend(),
            recording_filename=capture_file
        )
        gui = GUI(backend)
        locations_record = gui.capture_locations()
        backend = PlaybackBackend(recording_filename=capture_file)
        gui = GUI(backend)
        locations_playback = gui.capture_locations()
        assert locations_record == locations_playback

    def test_mouse_works(self):
        capture_file = os.path.join(
            _DIR,
            'test_mouse_works.log'
        )
        backend = RecordingBackend(
            source_backend=GeistFakeBackend(),
            recording_filename=capture_file
        )
        gui = GUI(backend)
        gui.click(Location(10, 10))
        backend = PlaybackBackend(recording_filename=capture_file)
        gui = GUI(backend)
        gui.click(Location(10, 10))

    def test_keyboard_works(self):
        capture_file = os.path.join(
            _DIR,
            'test_keyboard_works.log'
        )
        backend = RecordingBackend(
            source_backend=GeistFakeBackend(),
            recording_filename=capture_file
        )
        gui = GUI(backend)
        gui.key_presses('abcd')
        backend = PlaybackBackend(recording_filename=capture_file)
        gui = GUI(backend)
        gui.key_presses('abcd')

    @geist_replay
    def _decorated_method(self, gui):
        gui.key_presses('abcd')

    @unittest.skip("Need to mock get_platform_backend")
    def test_decorator(self):
        with EnvironmentContext(GEIST_REPLAY_MODE=_RECORD_MODE_ENV_VAR_VALUE):
            self._decorated_method()
        with EnvironmentContext(GEIST_REPLAY_MODE="playback"):
            self._decorated_method()


replay_suite = unittest.TestLoader().loadTestsFromTestCase(TestReplay)
all_tests = unittest.TestSuite([replay_suite])

if __name__ == "__main__":
    runner = unittest.TextTestRunner(verbosity=1)
    runner.run(all_tests)
