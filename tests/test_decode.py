import unittest
from pymtl3 import *
from pymtl3.stdlib import stream

from src.cl.fetch_stage import FetchPacket
from src.cl.decoder import DualMicroOp, MicroOp, Decode


class TestDecode(unittest.TestCase):
    def setUp(s) -> None:
        # runs before every test
        s.dut = Decode()
        s.dut.apply(DefaultPassGroup(textwave=True, linetrace=True))
        s.dut.sim_reset()

    def tearDown(s) -> None:
        # runs after every test
        if s.dut.sim_cycle_count():
            print("final:", s.dut.line_trace())
            s.dut.print_textwave()

    def test_simple_decode(s):
        inst1 = 0x0BEEF937  # lui x18, 0xDEAD
        inst2 = 0x012909B3  # add x19, x18, x18

        fp = FetchPacket(inst1, inst2)
        s.dut.fetch_packet @= fp

        s.dut.sim_eval_combinational()
        # s.dut.sim_tick()

        s.assertTrue(False)
