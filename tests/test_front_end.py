import unittest
from pymtl3 import *
from src.cl.front_end import FrontEnd

class TestFrontEnd(unittest.TestCase):
    def setUp(s) -> None:
        # runs before every test
        s.dut = FrontEnd()
        s.dut.apply(DefaultPassGroup(textwave=True, linetrace=True, vcdwave='vcd/test_front_end'))
        s.dut.sim_reset()

    def tearDown(s) -> None:
        # runs after every test
        if s.dut.sim_cycle_count():
            print("final:", s.dut.line_trace())
            s.dut.print_textwave()

    def test_simple_(s):
        s.dut.icache.load_file("tests/input_files/test_fetch256.csv")