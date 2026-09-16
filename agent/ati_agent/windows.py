"""Windows-only, privacy-preserving activity probes. No keystrokes or content are read."""
import ctypes, getpass, os, platform, socket, subprocess
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

def _gpu_metrics():
    try:
        result = subprocess.run(
            ['nvidia-smi', '--query-gpu=name,utilization.gpu,memory.used,memory.total', '--format=csv,noheader,nounits'],
            capture_output=True, text=True, timeout=3, check=True,
        )
        rows = [row.strip().split(', ') for row in result.stdout.splitlines() if row.strip()]
        if not rows: return {}
        name, utilization, memory_used, memory_total = rows[0]
        return {'gpu_name': name, 'gpu_percent': float(utilization), 'gpu_memory_used_mb': float(memory_used), 'gpu_memory_total_mb': float(memory_total)}
    except (OSError, subprocess.SubprocessError, ValueError):
        return {}

def metrics():
    memory = psutil.virtual_memory()
    frequency = psutil.cpu_freq()
    values = {
        'collected_at': __import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat(),
        'cpu_percent': psutil.cpu_percent(interval=None),
        'cpu_frequency_mhz': frequency.current if frequency else None,
        'cpu_frequency_max_mhz': frequency.max if frequency else None,
        'cpu_model': platform.processor() or platform.machine(),
        'cpu_logical_count': psutil.cpu_count(logical=True),
        'cpu_physical_count': psutil.cpu_count(logical=False),
        'ram_percent': memory.percent,
        'ram_used_mb': memory.used / 1024 / 1024,
        'ram_total_mb': memory.total / 1024 / 1024,
        'uptime_seconds': max(0, int(__import__('time').time() - psutil.boot_time())),
    }
    values.update(_gpu_metrics())
    return values
