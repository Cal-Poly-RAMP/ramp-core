import unittest
from pymtl3 import *

from src.cl.issue_queue import IssueQueue
from src.fl.util import one_hot

from src.common.interfaces import DualMicroOp, MicroOp
from src.common.consts import (
    B_TYPE,
    I_TYPE,
    J_TYPE,
    R_TYPE,
    S_TYPE,
    U_TYPE,
    NUM_PHYS_REGS,
    ISSUE_QUEUE_DEPTH,
)

NPR = NUM_PHYS_REGS


class TestIssueQueue(unittest.TestCase):
    def setUp(s) -> None:
        # runs before every test
        if not hasattr(s, "dut"):
            s.dut = IssueQueue()
            s.dut.apply(DefaultPassGroup(textwave=False, linetrace=True))
        s.dut.sim_reset()

    def tearDown(s) -> None:
        # runs after every test
        if s.dut.sim_cycle_count():
            print("final:", s.dut.line_trace())
            # s.dut.print_textwave()

    def test_multiple_add(s):
        # 1
        uop1 = MicroOp.from_bits(Bits(MicroOp.nbits, 0x12345678))
        uop1.valid @= 1
        uop2 = MicroOp.from_bits(Bits(MicroOp.nbits, 0))
        uop2.valid @= 0

        s.dut.duop_in @= DualMicroOp(uop1, uop2)
        s.dut.busy_table @= -1  # unable to be executed

        # Assert that was reset correctly
        s.assertEqual(s.dut.queue_empty, 1)
        s.assertEqual(s.dut.queue_full, 0)
        s.assertEqual(s.dut.tail, 0)

        # Assert that uop1 was added to queue, but uop2 was not
        s.dut.sim_tick()
        s.assertEqual(s.dut.queue_empty, 0)
        s.assertEqual(s.dut.tail, 1)
        s.assertEqual(s.dut.queue[0], uop1)

        # 2
        uop1 = MicroOp.from_bits(Bits(MicroOp.nbits, 0))
        uop1.valid @= 0
        uop2 = MicroOp.from_bits(Bits(MicroOp.nbits, 0x12345678))
        uop2.valid @= 1

        s.dut.duop_in @= DualMicroOp(uop1, uop2)
        s.dut.busy_table @= -1  # unable to be executed

        # Assert that uop2 was added to queue, but uop1 was not
        s.dut.sim_tick()
        s.assertEqual(s.dut.queue_empty, 0)
        s.assertEqual(s.dut.tail, 2)
        s.assertEqual(s.dut.queue[s.dut.tail - 1], uop2)

        # 3
        uop1 = MicroOp.from_bits(Bits(MicroOp.nbits, 0x2468ACE0))
        uop1.valid @= 1
        uop2 = MicroOp.from_bits(Bits(MicroOp.nbits, 0x13579BDF))
        uop2.valid @= 1

        s.dut.duop_in @= DualMicroOp(uop1, uop2)
        s.dut.busy_table @= -1  # unable to be executed

        # Assert that both were added to queue
        s.dut.sim_tick()
        s.assertEqual(s.dut.queue_empty, 0)
        s.assertEqual(s.dut.tail, 4)
        s.assertEqual(s.dut.queue[s.dut.tail - 2], uop1)
        s.assertEqual(s.dut.queue[s.dut.tail - 1], uop2)

    def test_fill(s):
        uop2 = MicroOp.from_bits(Bits(MicroOp.nbits, 0))
        uop2.valid @= 0

        s.dut.busy_table @= -1
        s.assertTrue(s.dut.queue_empty)
        s.assertFalse(s.dut.queue_full)

        for x in range(ISSUE_QUEUE_DEPTH):
            s.assertEqual(s.dut.tail, x)
            uop1 = MicroOp.from_bits(Bits(MicroOp.nbits, x))
            uop1.valid @= 1
            s.dut.duop_in @= DualMicroOp(uop1, uop2)
            s.dut.sim_tick()
            s.assertEqual(s.dut.queue_empty, 0)
            s.assertEqual(s.dut.queue[s.dut.tail - 1], uop1)

        s.assertTrue(s.dut.queue_full)
        s.assertFalse(s.dut.queue_empty)

    def test_issue_rsb_type(s):
        # prs1 and prs2 must be ready
        uop1 = MicroOp.from_bits(Bits(MicroOp.nbits, 0x2468ACE0))
        uop1.optype @= R_TYPE
        uop1.valid @= 1
        uop1.prs1 @= 1
        uop1.prs2 @= 2

        uop2 = MicroOp.from_bits(Bits(MicroOp.nbits, 0x13579BDF))
        uop2.optype @= R_TYPE
        uop2.valid @= 1
        uop2.prs1 @= 3
        uop2.prs2 @= 4

        uop3 = MicroOp.from_bits(Bits(MicroOp.nbits, 0xDEADBEEF))
        uop3.optype @= S_TYPE
        uop3.valid @= 1
        uop3.prs1 @= 5
        uop3.prs2 @= 6

        uop4 = MicroOp.from_bits(Bits(MicroOp.nbits, 0xBEEFDEAD))
        uop4.optype @= B_TYPE
        uop4.valid @= 1
        uop4.prs1 @= 7
        uop4.prs2 @= 8

        # adding uops to queues without executing
        s.dut.busy_table @= -1  # unable to be executed

        s.dut.duop_in @= DualMicroOp(uop1, uop2)
        s.dut.sim_tick()
        s.assertEqual(s.dut.uop_out.to_bits(), 0)

        s.dut.duop_in @= DualMicroOp(uop3, uop4)
        s.dut.sim_tick()
        s.assertEqual(s.dut.uop_out.to_bits(), 0)

        # executing uops out-of-order, while maintaining age-based priority
        s.dut.duop_in @= DualMicroOp.from_bits(Bits(DualMicroOp.nbits, 0))

        # uop3 and 4 ready
        s.dut.busy_table @= ~(
            one_hot(NPR, 5) | one_hot(NPR, 6) | one_hot(NPR, 7) | one_hot(NPR, 8)
        )
        s.dut.sim_tick()
        s.assertEqual(s.dut.uop_out, uop3)
        s.dut.sim_tick()
        s.assertEqual(s.dut.uop_out, uop4)

        s.dut.busy_table @= ~(one_hot(NPR, 3) | one_hot(NPR, 4))
        s.dut.sim_tick()
        s.assertEqual(s.dut.uop_out, uop2)

        s.dut.busy_table @= ~(one_hot(NPR, 1) | one_hot(NPR, 2))
        s.dut.sim_tick()
        s.assertEqual(s.dut.uop_out, uop1)

    def test_issue_i_type(s):
        # prs1 must be ready
        uop1 = MicroOp.from_bits(Bits(MicroOp.nbits, 0x2468ACE0))
        uop1.optype @= I_TYPE
        uop1.valid @= 1
        uop1.prs1 @= 1

        uop2 = MicroOp.from_bits(Bits(MicroOp.nbits, 0x13579BDF))
        uop2.optype @= I_TYPE
        uop2.valid @= 1
        uop2.prs1 @= 3

        uop3 = MicroOp.from_bits(Bits(MicroOp.nbits, 0xDEADBEEF))
        uop3.optype @= I_TYPE
        uop3.valid @= 1
        uop3.prs1 @= 5

        uop4 = MicroOp.from_bits(Bits(MicroOp.nbits, 0xBEEFDEAD))
        uop4.optype @= I_TYPE
        uop4.valid @= 1
        uop4.prs1 @= 7

        # adding uops to queues without executing
        s.dut.busy_table @= -1  # unable to be executed

        s.dut.duop_in @= DualMicroOp(uop1, uop2)
        s.dut.sim_tick()
        s.assertEqual(s.dut.uop_out.to_bits(), 0)

        s.dut.duop_in @= DualMicroOp(uop3, uop4)
        s.dut.sim_tick()
        s.assertEqual(s.dut.uop_out.to_bits(), 0)

        # executing uops out-of-order, while maintaining age-based priority
        s.dut.duop_in @= DualMicroOp.from_bits(Bits(DualMicroOp.nbits, 0))

        # uop3 and 4 ready
        s.dut.busy_table @= ~(one_hot(NPR, 5) | one_hot(NPR, 7))
        s.dut.sim_tick()
        s.assertEqual(s.dut.uop_out, uop3)
        s.dut.sim_tick()
        s.assertEqual(s.dut.uop_out, uop4)

        s.dut.busy_table @= ~one_hot(NPR, 3)
        s.dut.sim_tick()
        s.assertEqual(s.dut.uop_out, uop2)

        s.dut.busy_table @= ~one_hot(NPR, 1)
        s.dut.sim_tick()
        s.assertEqual(s.dut.uop_out, uop1)

    def test_issue_uj_type(s):
        # mem must be ready?
        uop1 = MicroOp.from_bits(Bits(MicroOp.nbits, 0x2468ACE0))
        uop1.optype @= U_TYPE
        uop1.valid @= 1

        uop2 = MicroOp.from_bits(Bits(MicroOp.nbits, 0x13579BDF))
        uop2.optype @= U_TYPE
        uop2.valid @= 1

        uop3 = MicroOp.from_bits(Bits(MicroOp.nbits, 0xDEADBEEF))
        uop3.optype @= J_TYPE
        uop3.valid @= 0

        uop4 = MicroOp.from_bits(Bits(MicroOp.nbits, 0xBEEFDEAD))
        uop4.optype @= J_TYPE
        uop4.valid @= 1

        # adding uops to queues while simultaneously executing
        s.dut.busy_table @= -1

        s.dut.duop_in @= DualMicroOp(uop1, uop2)
        s.dut.sim_tick()
        s.assertEqual(s.dut.uop_out, uop1)

        s.dut.duop_in @= DualMicroOp(uop3, uop4)
        s.dut.sim_tick()
        s.assertEqual(s.dut.uop_out, uop2)

        # executing uops out-of-order, while maintaining age-based priority
        s.dut.duop_in @= DualMicroOp.from_bits(Bits(DualMicroOp.nbits, 0))
        s.dut.sim_tick()
        s.assertEqual(s.dut.uop_out, uop4)

    def test_reset(s):
        s.dut.duop_in @= DualMicroOp.from_bits(Bits(DualMicroOp.nbits, 0xDEAD))
        s.dut.sim_tick()
        s.dut.sim_reset()
        s.assertEqual(s.dut.tail, 0)
        s.assertEqual(s.dut.queue_full, 0)
        s.assertEqual(s.dut.queue_empty, 1)
