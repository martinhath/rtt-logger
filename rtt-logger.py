import time
import subprocess
import threading
from sys import exit
from pynrfjprog.API import *
from pynrfjprog.MultiAPI import *

from sys import stdout, stderr

# put this in between the fields when outputting a message
MSG_DELIM = "\t"
# in case the delimiter is included in the actual message,
# replace it with this one
MSG_DELIM_REPLACE = "\\t"

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

    def __init__(self, devices=[]):

        if not devices:
            self._devices = [dev.decode('utf-8') for dev in subprocess.check_output(["nrfjprog", "-i"]).splitlines()]
        self._nrfs = []

    def _rtt_listener(self, device):
        nrf = MultiAPI(DeviceFamily.NRF51)

        CONTROL_BLOCK_ADDR = 0x20004a78

        nrf.open()
        # error('device number: ' + str(device))
        nrf.connect_to_emu_with_snr(int(device), 8000)
        nrf.sys_reset()
        nrf.go()
        # nrf.rtt_set_control_block_address(CONTROL_BLOCK_ADDR)
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
                nrf.recover()
                continue

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
    
    def start(self):
        threads = []

        for device in self._devices:
            thread = threading.Thread(target=self._rtt_listener, args=(device,))
            thread.daemon = True
            thread.start()
            threads.append(thread)

        time.sleep(2.1)
        for t in threads:
            t.join()


if __name__ == "__main__":
    from multiprocessing import freeze_support
    freeze_support()
    multilog = nRFMultiLogger()
    multilog.start()
