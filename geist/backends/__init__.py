import sys

def get_platform_backend():
    if sys.platform.startswith('win'):
        import geist.backends.windows
        return geist.backends.windows.GeistWindowsBackend()
    else:
        import geist.backends.xvfb
        return geist.backends.xvfb.GeistXvfbBackend(2)
