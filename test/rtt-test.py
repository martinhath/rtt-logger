import unittest
import time
import subprocess

import intelhex

from pynrfjprog.API import DeviceFamily
from pynrfjprog.MultiAPI import MultiAPI

BIN_FILE_PATH = 'test/fw-testing.bin'

class Test(unittest.TestCase):

    def __init__(self, testname, device):
        super(Test, self).__init__(testname)
        self.device = device
        nrf = MultiAPI(DeviceFamily.NRF51)
        nrf.open()
        nrf.connect_to_emu_with_snr(int(device))

        binfile = open(BIN_FILE_PATH , 'rb').read()
        bytes = binfile

        nrf.recover()
        nrf.write(0, map(ord, bytes), True)
        nrf.sys_reset()
        nrf.disconnect_from_emu()
        nrf.close()

    def setUp(self):
        nrf = MultiAPI(DeviceFamily.NRF51)
        nrf.open()
        nrf.connect_to_emu_with_snr(int(self.device))
        nrf.sys_reset()
        nrf.go()
        nrf.rtt_start()
        time.sleep(0.1)
        self.nrf = nrf

    def tearDown(self):
        self.nrf.rtt_stop()
        self.nrf.disconnect_from_emu()
        self.nrf.close()

    def test_find_control_block(self):
        self.assertTrue(self.nrf.rtt_is_control_block_found())
    
    def test_can_read(self):
        ret = self.nrf.rtt_read(0, 128)
        self.assertEquals(str(ret), 'Application Started\n')


if __name__ == '__main__':
    hexfile = intelhex.IntelHex('test/fw-testing.hex')
    hexfile.tofile(BIN_FILE_PATH, format='bin')

    devices = [dev.decode('utf-8') for dev in subprocess.check_output(["nrfjprog", "-i"]).splitlines()]

    suite = unittest.TestSuite()

    for device in devices:
        suite.addTest(Test('test_can_read', device))
        suite.addTest(Test('test_find_control_block', device))
        pass

    unittest.TextTestRunner().run(suite)
