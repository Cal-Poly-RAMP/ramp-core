import unittest
from pymtl3 import *
from hypothesis import given, strategies as st

from src.cl.dispatch import Dispatch
from src.cl.fetch_stage import FetchPacket
from src.cl.decoder import (
    DualMicroOp,
    MicroOp,
    Decode,
    NO_OP,
    INT_ISSUE_UNIT,
    MEM_ISSUE_UNIT,
)

class TestDispatch(unittest.TestCase):
    def setUp(self) -> None:
        # runs before each test
        self.dut = Dispatch()
        self.dut.apply(
            DefaultPassGroup(textwave=True, linetrace=True, vcdwave="vcd/test_dispatch")
        )
        self.dut.sim_reset()

    def tearDown(self) -> None:
        # runs after each test
        if self.dut.sim_cycle_count():
            print("final:", self.dut.line_trace())
            self.dut.print_textwave()

    @given(st.integers(min_value=0, max_value=2**DualMicroOp.nbits - 1))
    def test_forwarding_to_rob(self, i):
        # tests forwarding from dispatch to ROB
        duop = DualMicroOp.from_bits(Bits(DualMicroOp.nbits, i))
        self.dut.in_ @= duop
        self.dut.sim_eval_combinational()

        self.assertEqual(self.dut.to_rob, duop)

    def test_both_to_int(self):
        uop1, uop2 = MicroOp(), MicroOp()
        uop1.issue_unit = INT_ISSUE_UNIT
        uop2.issue_unit = INT_ISSUE_UNIT

        duop = DualMicroOp(uop1, uop2)
        self.dut.in_ @= duop
        self.dut.sim_eval_combinational()

        self.assertEqual(self.dut.to_int_issue, duop)
        self.assertEqual(self.dut.to_mem_issue, DualMicroOp(NO_OP, NO_OP))

    def test_both_to_mem(self):
        uop1, uop2 = MicroOp(), MicroOp()
        uop1.issue_unit = MEM_ISSUE_UNIT
        uop2.issue_unit = MEM_ISSUE_UNIT

        duop = DualMicroOp(uop1, uop2)
        self.dut.in_ @= duop
        self.dut.sim_eval_combinational()

        self.assertEqual(self.dut.to_mem_issue, duop)
        self.assertEqual(self.dut.to_int_issue, DualMicroOp(NO_OP, NO_OP))

    def test_mem_and_int(self):
        uop1, uop2 = MicroOp(), MicroOp()
        uop1.issue_unit = INT_ISSUE_UNIT
        uop2.issue_unit = MEM_ISSUE_UNIT

        duop = DualMicroOp(uop1, uop2)
        self.dut.in_ @= duop
        self.dut.sim_eval_combinational()

        self.assertEqual(self.dut.to_int_issue, DualMicroOp(uop1, NO_OP))
        self.assertEqual(self.dut.to_mem_issue, DualMicroOp(NO_OP, uop2))

    def test_no_op(self):
        self.dut.in_ @= DualMicroOp(NO_OP, NO_OP)
        self.dut.sim_eval_combinational()

        self.assertEqual(self.dut.to_int_issue, DualMicroOp(NO_OP, NO_OP))
        self.assertEqual(self.dut.to_mem_issue, DualMicroOp(NO_OP, NO_OP))
        self.assertEqual(self.dut.to_rob, DualMicroOp(NO_OP, NO_OP))