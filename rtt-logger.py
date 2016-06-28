import time
import subprocess
import threading
from sys import exit
from pynrfjprog.API import *
from pynrfjprog.MultiAPI import *


# put this in between the fields when outputting a message
MSG_DELIM = "\t"
# in case the delimiter is included in the actual message,
# replace it with this one
MSG_DELIM_REPLACE = "\\t"

stdout_lock = threading.Lock()
from sys import stdout, stderr
def write(s):
    # lock, in order to ensure that only one thread is writing at a time.
    # May not be needed
    stdout_lock.acquire()
    stdout.write(s)
    stdout.write('\n')
    stdout.flush()
    stdout_lock.release()

stderr_lock = threading.Lock()
def err(s):
    stdout_lock.acquire()
    stderr.write(s)
    stderr.write('\n')
    stderr.flush()
    stdout_lock.release()

    
class nRFMultiLogger(object):

    def __init__(self, devices=[]):

        if not devices:
            self._devices = [dev.decode('utf-8') for dev in subprocess.check_output(["nrfjprog", "-i"]).splitlines()]

        self._nrfs = []
    def _rtt_listener(self, device):
        nrf = MultiAPI(DeviceFamily.NRF51)

        # CONTROL_BLOCK_ADDR = 0x200026ec

        nrf.open()
        err('device number: ' + str(device))
        nrf.connect_to_emu_with_snr(int(device), 8000)
        nrf.sys_reset()
        nrf.go()
        # nrf.rtt_set_control_block_address(CONTROL_BLOCK_ADDR)
        nrf.rtt_start()
        time.sleep(1.1)

        self._nrfs.append(nrf)

        # print("Device %u %s"%(int(device), str()))

        if not nrf.rtt_is_control_block_found():
            err('Could not find control block for devie {}.'.format(device))
            return;

        try:
            # print('starting device ' + device)
            while True:
                try:
                    ret = nrf.rtt_read(0, 1024)

                    if ret == '':
                        continue

                    if type(ret) == int:
                        err("Error: bad data from device")
                        continue

                    for s in ret.split('\n'):
                        try:
                            level = "3"
                            timestamp, filename, line, msg = map(lambda s: s.strip(), s.split(","))
                        except Exception as e:
                            if s is "":
                                continue
                            err(e)
                            err(s, s.split(";"))
                            continue

                        msg = msg.replace(MSG_DELIM, MSG_DELIM_REPLACE).replace("\n", " ").strip()
                        f = MSG_DELIM.join([device, timestamp, filename + ':' + line, msg])
                        write(f)
                        
                except Exception as e:
                    err("Got exception: " + str(e))
                    nrf.recover()
                    if not nrf.is_connected_to_device():
                        # ??
                        err('not connected to device')

        except Exception as e:
            err("An error occured during printing: " + e.message)

        nrf.rtt_stop()
        nrf.disconnect_from_emu()
        nrf.close()

    def write(self, device, msg):
        if int(device) >= len(self._nrfs) or not len(msg):
            err("Invalid input: " + ret)
            return
        
        try:
            self._nrfs[int(device)].rtt_write(0, msg)

        except Exception as e:
            for nrf in self._nrfs:
                nrf.rtt_stop()
                nrf.disconnect_from_emu()
                nrf.close()
            err("An error occured while taking input: " + str(e))
    
    def start(self, cmd_line_mode=False):
        threads = []

        idx = 0
        for device in self._devices:
            device_id = 'SNR' + device + ": " + str(idx)
            err(device_id)

            thread = threading.Thread(target=self._rtt_listener,
                                      args=(device,))
            thread.daemon = True
            thread.start()
            threads.append(thread)
            idx += 1

        time.sleep(2.1)
        for t in threads:
            t.join()


if __name__ == "__main__":
    from multiprocessing import freeze_support
    freeze_support()
    multilog = nRFMultiLogger()
    multilog.start()
