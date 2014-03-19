import sys
import logging

logger = logging.getLogger(__name__)


def get_platform_backend(**kwargs):
    if sys.platform.startswith('win'):
        import geist.backends.windows
        return geist.backends.windows.GeistWindowsBackend(**kwargs)
    else:
        import geist.backends.xvfb
        if not 'display_num' in kwargs:
            kwargs['display_num'] = 2
        return geist.backends.xvfb.GeistXvfbBackend(**kwargs)
