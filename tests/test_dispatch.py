import unittest
from pymtl3 import *
from hypothesis import given, strategies as st

from src.cl.dispatch import Dispatch
from src.cl.decode import Decode

from src.common.interfaces import DualMicroOp, MicroOp, NO_OP
from src.common.consts import (
    B_TYPE,
    BRANCH_FUNCT_UNIT,
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

        self.assertEqual(self.dut.to_rob.uop1, duop.uop1)
        self.assertEqual(self.dut.to_rob.uop2, duop.uop2)

        # if duop.uop1.funct_unit != BRANCH_FUNCT_UNIT:
        #     self.assertEqual(self.dut.to_rob.uop1, duop.uop1)
        # else:
        #     self.assertEqual(self.dut.to_rob.uop1, MicroOp(0))

        # if duop.uop2.funct_unit != BRANCH_FUNCT_UNIT:
        #     self.assertEqual(self.dut.to_rob.uop2, duop.uop2)
        # else:
        #     self.assertEqual(self.dut.to_rob.uop2, MicroOp(0))

    def test_both_to_int(self):
        uop1, uop2 = MicroOp(), MicroOp()
        uop1.issue_unit @= INT_ISSUE_UNIT
        uop2.issue_unit @= INT_ISSUE_UNIT
        uop2.rob_idx @= 1

        duop = DualMicroOp(uop1, uop2)
        self.dut.in_ @= duop
        self.dut.rob_idx @= 0
        self.dut.mem_q_tail @= 0
        self.dut.sim_eval_combinational()

        self.assertEqual(self.dut.to_int_issue, duop)
        self.assertEqual(self.dut.to_mem_issue, DualMicroOp(NO_OP, NO_OP))

    def test_both_to_mem(self):
        uop1, uop2 = MicroOp(), MicroOp()
        uop1.issue_unit @= MEM_ISSUE_UNIT
        uop1.rob_idx @= 8
        uop1.mem_q_idx @= 1
        uop2.issue_unit @= MEM_ISSUE_UNIT
        uop2.rob_idx @= 2

        duop = DualMicroOp(uop1, uop2)
        self.dut.in_ @= duop
        self.dut.rob_idx @= 8
        self.dut.mem_q_tail @= 3
        self.dut.sim_eval_combinational()

        self.assertEqual(self.dut.to_mem_issue, duop)
        self.assertEqual(self.dut.to_int_issue, DualMicroOp(NO_OP, NO_OP))

    def test_mem_and_int(self):
        uop1, uop2 = MicroOp(), MicroOp()
        uop1.issue_unit @= INT_ISSUE_UNIT
        uop1.rob_idx @= 3
        uop1.mem_q_idx @= 0
        uop2.issue_unit @= MEM_ISSUE_UNIT
        uop2.rob_idx @= 4
        uop2.mem_q_idx @= 7

        duop = DualMicroOp(uop1, uop2)
        self.dut.in_ @= duop
        self.dut.rob_idx @= 3
        self.dut.mem_q_tail @= 8
        self.dut.sim_eval_combinational()

        self.assertEqual(self.dut.to_int_issue, DualMicroOp(uop1, NO_OP))
        self.assertEqual(self.dut.to_mem_issue, DualMicroOp(NO_OP, uop2))

    def test_no_op(self):
        self.dut.in_ @= DualMicroOp(NO_OP, NO_OP)
        self.dut.sim_eval_combinational()

        self.assertEqual(self.dut.to_int_issue, DualMicroOp(NO_OP, NO_OP))
        self.assertEqual(self.dut.to_mem_issue, DualMicroOp(NO_OP, NO_OP))
        self.assertEqual(self.dut.to_rob, DualMicroOp(NO_OP, NO_OP))
