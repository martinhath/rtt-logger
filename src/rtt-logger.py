import time
import subprocess
import threading
from sys import exit, argv
import getopt
from pynrfjprog.API import *
from pynrfjprog.MultiAPI import *

from sys import stdout, stderr

# put this in between the fields when outputting a message
MSG_DELIM = "\t"
# in case the delimiter is included in the actual message,
# replace it with this one
MSG_DELIM_REPLACE = "\\t"

# Seconds to wait when looking for devices
DEVICE_SEARCH_INTERVAL = 5

locks = {}
def _write(handle, s, device):
    # lock, in order to ensure that only one thread is writing at a time.
    # May not be needed
    if not handle in locks.keys():
        locks[handle] = threading.Lock()
    lock = locks[handle]
    with lock:
        handle.write(device)
        handle.write('\t')
        handle.write(s)
        if s[-1] != '\n':
            handle.write('\n')
        handle.flush()

def write(s, device='~~~'):
    if s:
        _write(stdout, s, device)

def error(s, device='~~~'):
    if s:
        _write(stderr, s, device)

class nRFMultiLogger(object):

    def __init__(self, devices=[], reset=False):

        self._devices = []
        for device in devices:
            self._devices.append(device)

        self._nrfs = []
        self.reset = reset

    def _rtt_listener(self, device):
        nrf = MultiAPI(DeviceFamily.NRF51)

        nrf.open()
        nrf.connect_to_emu_with_snr(int(device), 8000)
        if self.reset:
            nrf.sys_reset()
            nrf.go()
        nrf.rtt_start()
        time.sleep(1.1)

        self._nrfs.append(nrf)

        if not nrf.rtt_is_control_block_found():
            error('Could not find control block for devie {}.'.format(device))
            return;

        write('starting device', device)
        while True:
            try:
                ret = nrf.rtt_read(0, 1024)
            except Exception as e:
                error("Got exception: " + str(e))
                break;
                

            if not ret:
                continue

            split = ret.strip().split('\n')
            write(split[0], device)
            for line in split[1:]:
                # Skip only whitespace, but print with whitespace
                if line.strip():
                    write('\t' + line, device)

        nrf.rtt_stop()
        nrf.disconnect_from_emu()
        nrf.close()

        thread = threading.current_thread()
        self.threads.remove(thread)
        self._devices.remove(device)

    def find_devices(self):
        while True:
            nrf = MultiAPI(DeviceFamily.NRF51)
            nrf.open()
            devices = map(str, nrf.enum_emu_snr() or [])
            nrf.close()
            for device in devices:
                if device not in self._devices:
                    thread = threading.Thread(target=self._rtt_listener, args=(device,))
                    thread.daemon = True
                    thread.start()
                    self.threads.append(thread)
                    self._devices.append(device)
            time.sleep(DEVICE_SEARCH_INTERVAL)

    
    def start(self):
        self.threads = []

        device_searcher = threading.Thread(target=self.find_devices)
        device_searcher.daemon = True
        device_searcher.start()

        for device in self._devices:
            thread = threading.Thread(target=self._rtt_listener, args=(device,))
            thread.daemon = True
            thread.start()
            self.threads.append(thread)

        # never quit :)
        device_searcher.join()

if __name__ == "__main__":
    from multiprocessing import freeze_support
    freeze_support()
    try:
        opts, args = getopt.getopt(argv[1:], '', ['reset'])
    except getopt.GetoptError as err:
        print(str(err))
        exit(2)

    reset = False
    for (opt, _) in opts:
        if opt == '--reset':
            reset = True

    multilog = nRFMultiLogger(reset=reset)
    multilog.start()
