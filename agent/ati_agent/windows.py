"""Windows-only, privacy-preserving activity probes. No keystrokes or content are read."""
import ctypes, getpass, os, platform, socket
from ctypes import wintypes
import psutil
try:
    import win32gui, win32process
except ImportError: win32gui = win32process = None

class LASTINPUTINFO(ctypes.Structure): _fields_=[('cbSize',wintypes.UINT),('dwTime',wintypes.DWORD)]
def idle_seconds():
    info=LASTINPUTINFO(); info.cbSize=ctypes.sizeof(info); ctypes.windll.user32.GetLastInputInfo(ctypes.byref(info))
    return (ctypes.windll.kernel32.GetTickCount64()/1000)-(info.dwTime/1000)
def foreground():
    if not win32gui: return ('unknown', None)
    hwnd=win32gui.GetForegroundWindow(); title=win32gui.GetWindowText(hwnd) or None
    try:
        _,pid=win32process.GetWindowThreadProcessId(hwnd); return (psutil.Process(pid).name(),title)
    except (psutil.Error, OSError): return ('unknown',title)
def identity():
    hostname=socket.gethostname(); domain=os.environ.get('USERDOMAIN'); ips=[]
    for addrs in psutil.net_if_addrs().values(): ips += [a.address for a in addrs if a.family==socket.AF_INET and not a.address.startswith('127.')]
    return {'hostname':hostname,'domain':domain,'current_user':getpass.getuser(),'current_ip':ips[0] if ips else None,'os_version':platform.platform()}
