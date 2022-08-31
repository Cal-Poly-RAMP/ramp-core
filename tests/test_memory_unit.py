import unittest, pytest
from pymtl3 import *


from src.cl.memory_unit import MemoryUnit
from src.cl.dram import DRAM


class TestMemoryUnit(unittest.TestCase):
    def setUp(s) -> None:
        # runs before every test
        s.dut = MemoryUnit(queue_size=16, memory_size=16)
        s.dut.apply(
            DefaultPassGroup(
                textwave=True, linetrace=True, vcdwave="vcd/test_memory_unit"
            )
        )
        s.dut.sim_reset()

    def tearDown(s) -> None:
        # runs after every test
        if s.dut.sim_cycle_count():
            print("final:", s.dut.line_trace())
            s.dut.print_textwave()

    def test_byte_aligned(s):
        pass

