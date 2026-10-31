"""Read this process's resident memory without a monitoring dependency."""
from pathlib import Path
import sys


def parse_linux_status(text):
    values = {}
    for line in text.splitlines():
        name, _, value = line.partition(':')
        if name in ('VmRSS','VmHWM'):
            try:
                values[name] = float(value.split()[0]) / 1024.
            except (ValueError,IndexError):
                return None
    if not all(name in values for name in ('VmRSS','VmHWM')):
        return None
    return {'peak_rss_mib':round(values['VmHWM'],1),'rss_mib':round(values['VmRSS'],1),
            'memory_source':'proc-self-status'}


def process_memory():
    if sys.platform == 'linux':
        result = parse_linux_status(Path('/proc/self/status').read_text())
        if result is None: raise RuntimeError('Linux não informou o consumo deste processo.')
        return result
    if sys.platform == 'win32':
        import ctypes
        from ctypes import wintypes
        class Counters(ctypes.Structure):
            _fields_ = [('cb',wintypes.DWORD),('PageFaultCount',wintypes.DWORD),
                        ('PeakWorkingSetSize',ctypes.c_size_t),('WorkingSetSize',ctypes.c_size_t),
                        ('QuotaPeakPagedPoolUsage',ctypes.c_size_t),('QuotaPagedPoolUsage',ctypes.c_size_t),
                        ('QuotaPeakNonPagedPoolUsage',ctypes.c_size_t),('QuotaNonPagedPoolUsage',ctypes.c_size_t),
                        ('PagefileUsage',ctypes.c_size_t),('PeakPagefileUsage',ctypes.c_size_t)]
        kernel = ctypes.WinDLL('kernel32',use_last_error=True)
        psapi = ctypes.WinDLL('psapi',use_last_error=True)
        kernel.GetCurrentProcess.restype = wintypes.HANDLE
        psapi.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE,ctypes.POINTER(Counters),wintypes.DWORD]
        psapi.GetProcessMemoryInfo.restype = wintypes.BOOL
        counters = Counters()
        counters.cb = ctypes.sizeof(counters)
        if not psapi.GetProcessMemoryInfo(kernel.GetCurrentProcess(),ctypes.byref(counters),counters.cb):
            raise ctypes.WinError(ctypes.get_last_error())
        return {'peak_rss_mib':round(counters.PeakWorkingSetSize/1024**2,1),
                'rss_mib':round(counters.WorkingSetSize/1024**2,1),'memory_source':'GetProcessMemoryInfo'}
    raise RuntimeError('Contagem de RAM disponível em Linux e Windows.')
