import unittest
from pymtl3 import *

from src.cl.reorder_buffer import ROBEntryUop, ReorderBuffer, ROBEntry, ExecToROB
from src.cl.decode import (
    DualMicroOp,
    ROB_SIZE,
)

EMPTY_ROB_ENTRY = ROBEntry.from_bits(Bits(ROBEntry.nbits, 0))


class TestReorderBuffer(unittest.TestCase):
    def setUp(s) -> None:
        # runs before every test
        s.dut = ReorderBuffer()
        s.dut.apply(
            DefaultPassGroup(textwave=True, linetrace=True, vcdwave="vcd/test_decode")
        )
        s.maxDiff = None
        s.dut.sim_reset()

    def tearDown(s) -> None:
        # runs after every test
        if s.dut.sim_cycle_count():
            print("final:", s.dut.line_trace())
            s.dut.print_textwave()

    def test_write_to_rob(s):
        duop1 = DualMicroOp.from_bits(Bits(DualMicroOp.nbits, 0))
        duop1.uop1.valid @= 1
        duop1.uop2.valid @= 1
        s.dut.write_in @= duop1

        # initial behavior
        s.dut.sim_eval_combinational()
        s.assertEqual(s.dut.commit_out, EMPTY_ROB_ENTRY)
        s.assertEqual(s.dut.internal_rob_head, 0)
        s.assertEqual(s.dut.internal_rob_tail, 0)
        s.assertEqual(s.dut.rob_tail, 0)
        s.assertEqual(s.dut.instr_bank, [EMPTY_ROB_ENTRY for _ in range(ROB_SIZE // 2)])

        # write to rob
        s.dut.sim_tick()
        s.assertEqual(s.dut.commit_out, EMPTY_ROB_ENTRY)
        s.assertEqual(s.dut.internal_rob_head, 0)
        s.assertEqual(s.dut.internal_rob_tail, 1)  # internal table addr (1/2 external)
        s.assertEqual(s.dut.rob_tail, 2)  # external table addr (2* internal)

        s.assertEqual(
            s.dut.instr_bank[0],
            ROBEntry(
                pc=0,
                uop1_entry=ROBEntryUop(valid=1, busy=1, optype=0),
                uop2_entry=ROBEntryUop(valid=1, busy=1, optype=0),
            ),
        )

        # TODO: test multiple writes to rob

    def test_lifecycle(s):
        # write to rob
        duop1 = DualMicroOp.from_bits(Bits(DualMicroOp.nbits, 0))
        duop1.uop1.valid @= 1
        duop1.uop1.optype @= 2
        duop1.uop1.prd @= 1
        duop1.uop1.stale @= 1

        duop1.uop2.valid @= 1
        duop1.uop2.optype @= 3
        duop1.uop2.prd @= 2
        duop1.uop2.stale @= 2

        s.dut.write_in @= duop1
        s.dut.sim_tick()

        # checking that only writes when valid data
        for _ in range(2):
            s.dut.write_in @= DualMicroOp.from_bits(Bits(DualMicroOp.nbits, 0))
            s.dut.sim_tick()

            s.assertEqual(s.dut.commit_out, EMPTY_ROB_ENTRY)
            s.assertEqual(s.dut.internal_rob_head, 0)
            # internal table addr (1/2 external)
            s.assertEqual(s.dut.internal_rob_tail, 1)
            # external table addr (2* internal)
            s.assertEqual(s.dut.rob_tail, 2)

        # uop1 execution complete
        s.dut.op_complete @= ExecToROB(
            int_rob_idx=0, mem_rob_idx=0, int_rob_complete=1, mem_rob_complete=0
        )
        s.dut.sim_tick()

        # checking commited uop1
        s.assertEqual(s.dut.internal_rob_head, 0)
        s.assertEqual(s.dut.internal_rob_tail, 1)

        s.assertEqual(s.dut.commit_out.uop1_entry.busy, 0)
        s.assertEqual(s.dut.commit_out.uop1_entry.optype, 2)
        s.assertEqual(s.dut.commit_out.uop1_entry.prd, 1)
        s.assertEqual(s.dut.commit_out.uop1_entry.stale, 1)
        s.assertEqual(s.dut.commit_out.uop1_entry.valid, 1)
        s.assertEqual(s.dut.commit_out.uop2_entry.busy, 0)
        s.assertEqual(s.dut.commit_out.uop2_entry.optype, 0)
        s.assertEqual(s.dut.commit_out.uop2_entry.prd, 0)
        s.assertEqual(s.dut.commit_out.uop2_entry.stale, 0)
        s.assertEqual(s.dut.commit_out.uop2_entry.valid, 0)

        # uop2 execution complete
        s.dut.op_complete @= ExecToROB(
            int_rob_idx=0, mem_rob_idx=1, int_rob_complete=0, mem_rob_complete=1
        )
        s.dut.sim_tick()

        # checking that commit_out is valid
        s.assertEqual(s.dut.internal_rob_head, 1)
        s.assertEqual(s.dut.internal_rob_tail, 1)

        s.assertEqual(s.dut.commit_out.uop1_entry.busy, 0)
        s.assertEqual(s.dut.commit_out.uop1_entry.optype, 0)
        s.assertEqual(s.dut.commit_out.uop1_entry.prd, 0)
        s.assertEqual(s.dut.commit_out.uop1_entry.stale, 0)
        s.assertEqual(s.dut.commit_out.uop1_entry.valid, 0)
        s.assertEqual(s.dut.commit_out.uop2_entry.busy, 0)
        s.assertEqual(s.dut.commit_out.uop2_entry.optype, 3)
        s.assertEqual(s.dut.commit_out.uop2_entry.prd, 2)
        s.assertEqual(s.dut.commit_out.uop2_entry.stale, 2)
        s.assertEqual(s.dut.commit_out.uop2_entry.valid, 1)

    def test_overflow(s):
        duop1 = DualMicroOp.from_bits(Bits(DualMicroOp.nbits, 0))
        duop1.uop1.valid @= 1
        duop1.uop1.optype @= 2
        duop1.uop1.lrd @= 1
        duop1.uop1.stale @= 1

        duop1.uop2.valid @= 1
        duop1.uop2.optype @= 3
        duop1.uop2.lrd @= 2
        duop1.uop2.stale @= 2

        s.dut.write_in @= duop1

        # filling rob
        for x in range(ROB_SIZE // 2 - 1):
            s.assertEqual(s.dut.rob_tail, 2 * x)
            s.assertEqual(s.dut.internal_rob_head, 0)
            s.assertFalse(s.dut.bank_full)
            s.dut.sim_tick()
            s.assertFalse(s.dut.bank_empty)

        # overflow
        with s.assertRaises(OverflowError):
            s.assertFalse(s.dut.bank_empty)
            s.dut.sim_tick()
            s.assertFalse(s.dut.bank_full)

        # emptying rob
        s.dut.write_in @= DualMicroOp.from_bits(Bits(DualMicroOp.nbits, 0))
        for x in range(ROB_SIZE):
            s.assertFalse(s.dut.bank_empty)
            s.dut.op_complete @= ExecToROB(
                int_rob_idx=x, mem_rob_idx=0, int_rob_complete=1, mem_rob_complete=0
            )
            s.dut.sim_tick()

        s.assertEqual(s.dut.internal_rob_head, s.dut.internal_rob_tail)
        s.assertFalse(s.dut.bank_full)
        s.assertTrue(s.dut.bank_empty)

        # TODO: test reset
