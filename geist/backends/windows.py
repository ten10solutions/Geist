from __future__ import division, absolute_import, print_function
import numpy
import subprocess
import shlex
import ctypes
from ctypes import (
    byref,
    WINFUNCTYPE,
    c_ubyte,
    sizeof,
    POINTER,
    Structure,
)
from ctypes.wintypes import (
    POINT,
    RECT,
    DWORD,
    LPARAM,
    HWND,
    BOOL,
    WCHAR,
    LONG,
    WORD
)
from geist.core import Location, LocationList
from ._common import BackendActionBuilder
from . import logger


class _ActionsTransaction(object):
    def __init__(self, backend):
        self._actions_builder = BackendActionBuilder(backend)

    def __enter__(self):
        return self._actions_builder

    def __exit__(self, *args):
        self._actions_builder.execute()
        return False


_USER32 = ctypes.windll.USER32
_GDI32 = ctypes.windll.GDI32


class _RGBQUAD(Structure):
    _fields_ = [
        ('rgbBlue', c_ubyte),
        ('rgbGreen', c_ubyte),
        ('rgbRed', c_ubyte),
        ('rgbReserved', c_ubyte),
    ]


class _BITMAPINFOHEADER(Structure):
    _fields_ = [
        ('biSize', DWORD),
        ('biWidth', LONG),
        ('biHeight', LONG),
        ('biPlanes', WORD),
        ('biBitCount', WORD),
        ('biCompression', WORD),
        ('biSizeImage', DWORD),
        ('biXPelsPerMeter', LONG),
        ('biYPelsPerMeter', LONG),
        ('biClrUsed', DWORD),
        ('biClrImportant', DWORD)
    ]


class _BITMAPINFO(Structure):
    _fields_ = [
        ('bmiHeader', _BITMAPINFOHEADER),
        ('bmiColors', (_RGBQUAD * 1))
    ]


_DIB_RGB_COLORS = 0


class GeistWindowsBackend(object):
    SRCCOPY = 0xCC0020
    SM_CXVIRTUALSCREEN, SM_CYVIRTUALSCREEN = 78, 79
    BITSPIXEL = 12

    def __init__(self, **kwargs):
        self._mouse = _Mouse()
        self._keyboard = _KeyBoard()
        logger.info("Created GeistWindowsBackend")

    def create_process(self, command):
        dev_null = open('NUL', 'w')
        process = subprocess.Popen(
            shlex.split(command), stdout=dev_null, stderr=subprocess.STDOUT
        )
        return Process(process.pid)

    def actions_transaction(self):
        return _ActionsTransaction(self)

    def capture_locations(self):
        hwnd = _USER32.GetDesktopWindow()
        width, height = (
            _USER32.GetSystemMetrics(GeistWindowsBackend.SM_CXVIRTUALSCREEN),
            _USER32.GetSystemMetrics(GeistWindowsBackend.SM_CYVIRTUALSCREEN)
        )
        desktop_dc = _USER32.GetWindowDC(hwnd)
        capture_dc = _GDI32.CreateCompatibleDC(desktop_dc)

        # Check that the screen has bit depth of 32
        bits = _GDI32.GetDeviceCaps(desktop_dc, GeistWindowsBackend.BITSPIXEL)
        if bits != 32:
            raise NotImplementedError(
                "Geist only supports displays with a bit depth of 32 (%d)"
                % bits)

        bmp = _GDI32.CreateCompatibleBitmap(desktop_dc, width, height)
        _GDI32.SelectObject(capture_dc, bmp)
        _GDI32.BitBlt(
            capture_dc, 0, 0, width, height, desktop_dc, 0, 0,
            GeistWindowsBackend.SRCCOPY
        )

        bmp_info = _BITMAPINFO()
        bmp_info.bmiHeader.biSize = sizeof(bmp_info)
        bmp_info.bmiHeader.biPlanes = 1
        bmp_info.bmiHeader.biBitCount = 32

        bmp_info.bmiHeader.biWidth = width
        bmp_info.bmiHeader.biHeight = -height

        memarray = numpy.ndarray((height, width), dtype='4B')
        _GDI32.GetDIBits(
            capture_dc,
            bmp,
            0,
            height,
            memarray.ctypes.data_as(POINTER(c_ubyte)),
            byref(bmp_info),
            _DIB_RGB_COLORS
        )
        _GDI32.DeleteObject(bmp)
        _GDI32.DeleteDC(capture_dc)
        _GDI32.DeleteDC(desktop_dc)
        #strip alpha and reverse bgr to rgb
        image = memarray[:, :, 2::-1]
        return LocationList([Location(0, 0, width, height, image=image)])

    def key_down(self, name):
        self._keyboard.key_down(name)

    def key_up(self, name):
        self._keyboard.key_up(name)

    def button_down(self, button_num):
        self._mouse.button_down(button_num)

    def button_up(self, button_num):
        self._mouse.button_up(button_num)

    def move(self, point):
        self._mouse.move(point)

    def close(self):
        pass

    def __del__(self):
        self.close()


class _KeyBoard(object):
    KEYEVENTF_KEYUP = 0x0002
    KEYEVENTF_KEYDOWN = 0x0000
    VK_SHIFT = 0x10
    VK_CONTROL = 0x11
    VK_MENU = 0x12
    VK_RETURN = 0x0D

    CHAR_TO_NAME_MAP = {
        'return': '\r',
        'space': ' ',
        'tab': '\t',
        'period': '.',
        'minus': '-'
    }

    def _convert_keyname_to_virtual_key(self, name):
        if name == 'shift':
            return _KeyBoard.VK_SHIFT
        elif name == 'menu':
            return _KeyBoard.VK_MENU
        elif name == 'control':
            return _KeyBoard.VK_CONTROL
        elif name in _KeyBoard.CHAR_TO_NAME_MAP:
            return _USER32.VkKeyScanW(
                WCHAR(_KeyBoard.CHAR_TO_NAME_MAP[name])
            ) & 0xFF
        else:
            return _USER32.VkKeyScanW(WCHAR(name)) & 0xFF

    def key_down(self, name):
        vkey = self._convert_keyname_to_virtual_key(name)
        _USER32.keybd_event(vkey, 0, _KeyBoard.KEYEVENTF_KEYDOWN, None)

    def key_up(self, name):
        vkey = self._convert_keyname_to_virtual_key(name)
        _USER32.keybd_event(vkey, 0, _KeyBoard.KEYEVENTF_KEYUP, None)


class _Mouse(object):
    MOUSEEVENTF_MOVE = 0x0001
    MOUSEEVENTF_LEFTDOWN = 0x0002
    MOUSEEVENTF_LEFTUP = 0x0004
    MOUSEEVENTF_RIGHTDOWN = 0x0008
    MOUSEEVENTF_RIGHTUP = 0x0010
    MOUSEEVENTF_MIDDLEDOWN = 0x0020
    MOUSEEVENTF_MIDDLEUP = 0x0040
    MOUSEEVENTF_WHEEL = 0x0800
    MOUSEEVENTF_VIRTUALDESK = 0x4000
    MOUSEEVENTF_ABSOLUTE = 0x8000

    SPI_SETMOUSE = 0x0004
    SPI_SETMOUSESPEED = 0x0071

    SM_CXSCREEN = 0
    SM_CYSCREEN = 1

    LEFT_BUTTON, MIDDLE_BUTTON, RIGHT_BUTTON = [1, 2, 3]

    def _normalize_coords(self, point):
        norm = 65535
        x, y = point
        w = _USER32.GetSystemMetrics(_Mouse.SM_CXSCREEN)
        h = _USER32.GetSystemMetrics(_Mouse.SM_CYSCREEN)
        return (int(x * (norm / w)), int(y * (norm/h)))

    def move(self, point):
        self._current_point = point
        x, y = self._normalize_coords(point)        
        _USER32.SetCursorPos(*point)

    def scroll(lines):
        _USER32.mouse_event(
            _Mouse.MOUSEEVENTF_WHEEL,
            0,
            0,
            int(120 * lines),
            None
        )

    def button_down(self, button):
        _USER32.mouse_event(self._map_button_down(button), 0, 0, 0, None)

    def button_up(self, button):
        _USER32.mouse_event(self._map_button_up(button), 0, 0, 0, None)

    def _map_button_down(self, button):
        assert button in [
            _Mouse.LEFT_BUTTON,
            _Mouse.MIDDLE_BUTTON,
            _Mouse.RIGHT_BUTTON
        ]
        return [
            _Mouse.MOUSEEVENTF_LEFTDOWN,
            _Mouse.MOUSEEVENTF_MIDDLEDOWN,
            _Mouse.MOUSEEVENTF_RIGHTDOWN
        ][button - 1]

    def _map_button_up(self, button):
        assert button in [
            _Mouse.LEFT_BUTTON,
            _Mouse.MIDDLE_BUTTON,
            _Mouse.RIGHT_BUTTON
        ]
        return [
            _Mouse.MOUSEEVENTF_LEFTUP,
            _Mouse.MOUSEEVENTF_MIDDLEUP,
            _Mouse.MOUSEEVENTF_RIGHTUP
        ][button - 1]


_EnumWindowsProc = WINFUNCTYPE(BOOL, HWND, LPARAM)


def hwnd_to_pid(hwnd):
    pid = DWORD()
    _USER32.GetWindowThreadProcessId(int(hwnd), byref(pid))
    return pid.value


class Process(object):
    def __init__(self, pid):
        self.__pid = int(pid)

    @property
    def pid(self):
        return self.__pid

    def destroy(self):
        subprocess.call(
            'taskkill /F /T /PID %d' % (self.pid),
            shell=True
        )

    def get_window(self):
        found_hwnd = []

        def callback(hwnd, data):
            found_pid = hwnd_to_pid(hwnd)
            if found_pid == self.pid:
                found_hwnd.append(hwnd)
                return False
            return True
        _USER32.EnumWindows(_EnumWindowsProc(callback), 0)
        if found_hwnd:
            return Window(found_hwnd[0]).get_root()
        return None


def get_all_windows():
    windows = []

    def callback(hwnd, data):
        windows.append(Window(hwnd))
        return True
    _USER32.EnumDesktopWindows(None, _EnumWindowsProc(callback), 0)
    return windows


def get_window_at(x, y):
    point = POINT()
    point.x, point.y = x, y
    hwnd = ctypes.windll.user32.WindowFromPoint(point)
    if not hwnd:
        return None
    else:
        return Window(hwnd)


class Window(object):
    SWP_NOOWNERZORDER = 0x0200
    SWP_NOSENDCHANGING = 0x0400

    SW_SHOWMAXIMIZED = 3
    SW_SHOWMINIMIZED = 2

    BITSPIXEL = 12

    def __init__(self, hwnd):
        self.__hwnd = int(hwnd)

    def _rect(self):
        rect = RECT()
        _USER32.GetWindowRect(self.__hwnd, byref(rect))
        return (
            rect.left,
            rect.top,
            (rect.right - rect.left),
            (rect.bottom - rect.top),
        )

    def set_position(self, rect):
        x, y, w, h = rect
        _USER32.SetWindowPos(
            self.__hwnd,
            0,
            x,
            y,
            w,
            h,
            Window.SWP_NOSENDCHANGING | Window.SWP_NOOWNERZORDER
        )

    @property
    def title(self):
        max_len = 128
        text = (WCHAR*max_len)()
        _USER32.GetWindowTextW(self.__hwnd, text, max_len)
        return text.value

    @property
    def classname(self):
        max_len = 128
        text = (WCHAR*max_len)()
        _USER32.GetClassNameW(self.__hwnd, text, max_len)
        return text.value

    @property
    def visible(self):
        return bool(_USER32.IsWindowVisible(self.__hwnd))

    def switch_to(self):
        _USER32.SwitchToThisWindow(self.__hwnd, False)

    def maximise(self):
        """Maximise the window and return True if previously visible"""
        return bool(_USER32.ShowWindow(self.__hwnd, Window.SW_SHOWMAXIMIZED))

    def minimise(self):
        """Minimise the window and return True if previously visible"""
        return bool(_USER32.ShowWindow(self.__hwnd, Window.SW_SHOWMINIMIZED))

    def get_process(self):
        return Process(hwnd_to_pid(self.__hwnd))

    def get_root(self):
        hwnd = self.__hwnd
        while _USER32.GetParent(hwnd):
            hwnd = _USER32.GetParent(hwnd)
        if hwnd == self.__hwnd:
            return self
        else:
            return Window(hwnd)

    def __hash__(self):
        return self.__hwnd

    def __eq__(self, other):
        try:
            return self.__hwnd == other.__hwnd
        except:
            return False

    def capture_locations(self):
        x, y, width, height = self._rect()
        window_dc = _USER32.GetWindowDC(self.__hwnd)
        capture_dc = _GDI32.CreateCompatibleDC(window_dc)

        # Check that the screen has bit depth of 32
        bits = _GDI32.GetDeviceCaps(window_dc, Window.BITSPIXEL)
        if bits != 32:
            raise NotImplementedError(
                "Geist only supports displays with a bit depth of 32 (%d)"
                % bits)

        bmp = _GDI32.CreateCompatibleBitmap(window_dc, width, height)
        _GDI32.SelectObject(capture_dc, bmp)
        _USER32.PrintWindow(self.__hwnd, capture_dc, 0)

        bmp_info = _BITMAPINFO()
        bmp_info.bmiHeader.biSize = sizeof(bmp_info)
        bmp_info.bmiHeader.biPlanes = 1
        bmp_info.bmiHeader.biBitCount = 32

        bmp_info.bmiHeader.biWidth = width
        bmp_info.bmiHeader.biHeight = -height

        memarray = numpy.ndarray((height, width), dtype='4B')
        _GDI32.GetDIBits(
            capture_dc,
            bmp,
            0,
            height,
            memarray.ctypes.data_as(POINTER(c_ubyte)),
            byref(bmp_info),
            _DIB_RGB_COLORS
        )

        _GDI32.DeleteObject(bmp)
        _GDI32.DeleteDC(capture_dc)
        _GDI32.DeleteDC(window_dc)

        #strip alpha and reverse bgr to rgb
        image = memarray[:, :, 2::-1]
        return LocationList([Location(x, y, width, height, image=image)])

    def get_child_window_at(self, x, y):
        point = POINT()
        point.x, point.y = x, y
        child_hwnd = ctypes.windll.user32.RealChildWindowFromPoint(
            self.__hwnd,
            point
        )
        if not child_hwnd:
            return None
        else:
            return Window(child_hwnd)

    def client_area_rect(self):
        client_rect = RECT()
        win_rect = RECT()
        offset = POINT()

        _USER32.GetClientRect(self.__hwnd, byref(client_rect))
        _USER32.GetWindowRect(self.__hwnd, byref(win_rect))
        _USER32.ClientToScreen(self.__hwnd, byref(offset))

        x = offset.x - win_rect.left
        y = offset.y - win_rect.top
        w = client_rect.right
        h = client_rect.bottom
        return x, y, w, h

    def __repr__(self):
        return "Window(hwnd=%r, title=%r, classname=%r)" % (
            self.__hwnd, self.title, self.classname
        )
