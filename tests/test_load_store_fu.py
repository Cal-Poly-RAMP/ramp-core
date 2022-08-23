import unittest
from pymtl3 import *

from src.cl.decode import Decode
from src.cl.load_store_fu import LoadStoreFU


class TestDecode(unittest.TestCase):
    def setUp(s) -> None:
        # runs before every test
        s.dut = LoadStoreFU()
        s.dut.apply(
            DefaultPassGroup(
                textwave=True, linetrace=True, vcdwave="vcd/test_load_store_fu"
            )
        )
        s.dut.sim_reset()
        s.maxDiff = None

    def tearDown(s) -> None:
        # runs after every test
        if s.dut.sim_cycle_count():
            print("final:", s.dut.line_trace())
            s.dut.print_textwave()

    def test_decode_lb(s):
        pass
