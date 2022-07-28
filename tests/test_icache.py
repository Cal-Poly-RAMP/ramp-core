import unittest
from hypothesis import given, strategies as st
from pymtl3 import *
from src.cl.icache import ICache


class TestICache(unittest.TestCase):
    dpw = 8  ## hardcoded for now. data per word for icache 64 / 8

    def setUp(self):
        self.dut = ICache()
        self.dut.apply(DefaultPassGroup())
        self.dut.sim_reset()

    @given(st.integers(min_value=0, max_value=2**8 - dpw - 1))
    def test(self, addr):
        self.dut.memory.load_file("tests/input_files/test_icache256.csv")
        self.dut.addr @= addr
        self.dut.sim_tick()

        self.assertEqual(
            self.dut.data_out, 0x0100010001000100 if addr % 2 else 0x0001000100010001
        )
