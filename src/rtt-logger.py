from sys import exit, argv, stdout, stderr
import getopt
import signal
import threading
import time

from pynrfjprog.API import *
from pynrfjprog.MultiAPI import *


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

def debug(s, device='~~~'):
    if s:
        _write(stdout, s, device)


class RTTLogger(object):

    def __init__(self, reset=False, event=threading.Event()):
        self.reset = reset
        self.event = event

    def rtt_loop(self, device):
        with MultiAPI(DeviceFamily.NRF51) as nrf:
            nrf.connect_to_emu_with_snr(int(device), 8000)
            if self.reset:
                nrf.sys_reset()
                nrf.go()
            nrf.rtt_start()
            time.sleep(2)

            if not nrf.rtt_is_control_block_found():
                error('Could not find control block for devie {}.'.format(device))
            else:
                write('Connected to ' + device)
                while not self.event.is_set():
                    try:
                        ret = nrf.rtt_read(0, 1024)
                    except Exception as e:
                        error("Got exception: " + str(e))
                        break;

                    if not ret:
                        time.sleep(0.1)
                        continue

                    split = ret.strip().split('\n')
                    write(split[0], device)
                    for line in split[1:]:
                        # Skip only whitespace, but print with whitespace
                        if line.strip():
                            # output is the format <device>\t<message>
                            write('\t' + line, device)
                write('Disconnected from ' + device)
            nrf.rtt_stop()
            nrf.disconnect_from_emu()

    def get_devices(self):
        with MultiAPI(DeviceFamily.NRF51) as nrf:
            devices = nrf.enum_emu_snr()
            if not devices:
                return []
            nrf.connect_to_emu_without_snr()
            if type(devices) != list:
                raise Exception('enum_emu_snr didn\'t return a list')
            nrf.disconnect_from_emu()
        return list(map(str, devices))

    def start(self):
        devices = self.get_devices()
        if not devices:
            return

        self.threads = []
        for device in devices:
            thread = threading.Thread(target=self.rtt_loop, args=(device,))
            thread.start()
            self.threads.append(thread)

        while not self.event.is_set():
            time.sleep(1)


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

    event = threading.Event()
    signal.signal(signal.SIGINT, lambda s, f: event.set())

    logger = RTTLogger(reset=reset, event=event)
    logger.start()
