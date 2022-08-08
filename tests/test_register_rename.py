import unittest
from pymtl3 import *

from src.cl.register_rename import (
    NUM_ISA_REGS,
    RegisterRename,
    LogicalRegs,
    PhysicalRegs,
    NUM_PHYS_REGS,
)


class TestRegisterRename(unittest.TestCase):
    def setUp(self) -> None:
        # runs before every test
        if not hasattr(self, "dut"):
            self.dut = RegisterRename()
            self.dut.apply(DefaultPassGroup(textwave=True, linetrace=True))
        # vcdwave='RegRename'
        self.dut.sim_reset()

    def tearDown(self) -> None:
        # runs after every test
        print("final:", self.dut.line_trace())
        self.dut.print_textwave()

    def test_simple_dest_rename(self):
        # making sure multiple renamed registers are not equal
        inst1_lregs = LogicalRegs(lrd=18, lrs1=0, lrs2=0)
        inst2_lregs = LogicalRegs(lrd=19, lrs1=0, lrs2=0)
        self.dut.inst1_lregs @= inst1_lregs
        self.dut.inst2_lregs @= inst2_lregs

        self.dut.sim_eval_combinational()

        assigned_regs = []
        for w in [
            self.dut.inst2_pregs.prd,
            self.dut.inst1_pregs.prd,
        ]:
            self.assertNotIn(w.uint(), assigned_regs)
            self.assertNotEqual(w.uint(), 0)
            assigned_regs.append(w.uint())

        self.assertEqual(self.dut.inst1_pregs.prs1.uint(), 0)
        self.assertEqual(self.dut.inst1_pregs.prs2.uint(), 0)
        self.assertEqual(self.dut.inst2_pregs.prs1.uint(), 0)
        self.assertEqual(self.dut.inst2_pregs.prs2.uint(), 0)

    def test_multiple_rename(self):
        # test that stale registers are deallocated, for either set of the two instructions
        a = LogicalRegs(lrd=5, lrs1=0, lrs2=0)  # (inst1) allocate 1
        b = LogicalRegs(lrd=6, lrs1=0, lrs2=0)  # (isnt2) allocate 2

        c = LogicalRegs(lrd=7, lrs1=0, lrs2=0)  # (inst1) reallocate 1
        d = LogicalRegs(lrd=8, lrs1=0, lrs2=0)  # (inst2) reallocate 2

        self.dut.inst1_lregs @= a
        self.dut.inst2_lregs @= b
        self.dut.sim_eval_combinational()

        prd1_1 = self.dut.inst1_pregs.prd.uint()
        prd2_1 = self.dut.inst2_pregs.prd.uint()

        self.dut.sim_tick()  # clock tick to commit state

        self.dut.inst1_lregs @= c
        self.dut.inst2_lregs @= d
        self.dut.sim_eval_combinational()

        prd1_2 = self.dut.inst1_pregs.prd.uint()
        prd2_2 = self.dut.inst2_pregs.prd.uint()

        # testing that reallocated phys regs are not the same as previously allocated
        self.assertNotEqual(prd1_1, prd1_2)
        self.assertNotEqual(prd2_1, prd2_2)
        self.assertNotEqual(prd1_1, 0)
        self.assertNotEqual(prd2_1, 0)
        self.assertNotEqual(prd1_2, 0)
        self.assertNotEqual(prd2_2, 0)

    def test_dest_src_rename(self):
        # making sure that src registers point to renamed dest registers from previous instructions
        d = self.dut

        a = LogicalRegs(lrd=18, lrs1=0, lrs2=0)
        b = LogicalRegs(lrd=19, lrs1=0, lrs2=0)
        c = LogicalRegs(lrd=20, lrs1=18, lrs2=19)
        e = LogicalRegs(lrd=21, lrs1=19, lrs2=18)

        self.dut.inst1_lregs @= a
        self.dut.inst2_lregs @= b
        d.sim_eval_combinational()

        prd1 = d.inst1_pregs.prd.uint()
        prd2 = d.inst2_pregs.prd.uint()

        d.sim_tick()  # clock tick to commit state

        self.dut.inst1_lregs @= c
        self.dut.inst2_lregs @= e
        d.sim_eval_combinational()

        self.assertEqual(prd1, d.inst1_pregs.prs1.uint())
        self.assertEqual(prd2, d.inst1_pregs.prs2.uint())
        self.assertEqual(prd1, d.inst2_pregs.prs2.uint())
        self.assertEqual(prd2, d.inst2_pregs.prs1.uint())

        self.dut.print_textwave()

    def test_simultaneous_renaming(self):
        # testing renaming dependencies when 2 dependent instructions are being renamed at the same time
        # making sure that src registers point to renamed dest registers from previous instructions
        d = self.dut

        inst1_lregs = LogicalRegs(lrd=5, lrs1=0, lrs2=0)
        inst2_lregs = LogicalRegs(lrd=6, lrs1=5, lrs2=5)
        self.dut.inst1_lregs @= inst1_lregs
        self.dut.inst2_lregs @= inst2_lregs

        self.dut.sim_eval_combinational()

        # source registers from inst 2 point to inst 1
        self.assertEqual(d.inst1_pregs.prd.uint(), d.inst2_pregs.prs1.uint())
        self.assertEqual(d.inst1_pregs.prd.uint(), d.inst2_pregs.prs2.uint())

    def test_stale(self):
        # test that stale registers are deallocated, for either set of the two instructions
        a = LogicalRegs(lrd=5, lrs1=0, lrs2=0)  # (inst1) allocate 1
        b = LogicalRegs(lrd=6, lrs1=5, lrs2=5)  # (isnt2) allocate 2

        c = LogicalRegs(lrd=5, lrs1=6, lrs2=6)  # (inst1) reallocate 1
        d = LogicalRegs(lrd=6, lrs1=5, lrs2=5)  # (inst2) reallocate 2

        self.dut.inst1_lregs @= a
        self.dut.inst2_lregs @= b

        self.dut.sim_eval_combinational()
        prd1_1 = self.dut.inst1_pregs.prd.uint()
        prd2_1 = self.dut.inst2_pregs.prd.uint()
        self.dut.sim_tick()  # clock tick to commit state

        self.dut.inst1_lregs @= c
        self.dut.inst2_lregs @= d

        self.dut.sim_eval_combinational()

        # testing that reallocated phys regs are not the same as previously allocated
        self.assertNotEqual(prd1_1, self.dut.inst1_pregs.prd.uint())
        self.assertNotEqual(prd2_1, self.dut.inst2_pregs.prd.uint())
        # testing that previously allocated registers are now "stale"
        self.assertEqual(prd1_1, self.dut.inst1_pregs.stale.uint())
        self.assertEqual(prd2_1, self.dut.inst2_pregs.stale.uint())

    def test_busy_table_freelist_maptable(self):
        # test that register marked busy **when it leaves the freelist**
        # TODO: test that register is marked as not busy when it completes
        ALL_HIGH = Bits(NUM_PHYS_REGS, -1)
        ONE = Bits(NUM_PHYS_REGS, 1)

        a = LogicalRegs(lrd=0, lrs1=0, lrs2=0)  # noop
        b = LogicalRegs(lrd=1, lrs1=0, lrs2=0)

        c = LogicalRegs(lrd=0, lrs1=0, lrs2=0)  # noop
        d = LogicalRegs(lrd=1, lrs1=0, lrs2=0)

        e = LogicalRegs(lrd=2, lrs1=0, lrs2=0)
        f = LogicalRegs(lrd=3, lrs1=0, lrs2=0)

        self.dut.inst1_lregs @= a
        self.dut.inst2_lregs @= b
        self.dut.sim_tick()

        self.assertEqual(self.dut.free_list, ALL_HIGH << 2)
        self.assertTrue(self.dut.busy_table & (ONE << 1))
        # testing that logical x0 registers point to physical x0 registers
        self.assertEqual(self.dut.inst1_pregs.prs1, 0)
        self.assertEqual(self.dut.inst1_pregs.prs2, 0)
        self.assertEqual(self.dut.inst1_pregs.stale, 0)
        self.assertEqual(self.dut.inst2_pregs.prs1, 0)
        self.assertEqual(self.dut.inst2_pregs.prs2, 0)

        self.dut.inst1_lregs @= c
        self.dut.inst2_lregs @= d
        self.dut.sim_tick()

        self.assertEqual(self.dut.free_list, ALL_HIGH << 3)
        self.assertTrue(self.dut.busy_table & (ONE << 1 | ONE << 2))
        # testing that logical x0 registers point to physical x0 registers
        self.assertEqual(self.dut.inst1_pregs.stale, 0)
        self.assertEqual(self.dut.inst1_pregs.prs1, 0)
        self.assertEqual(self.dut.inst1_pregs.prs2, 0)
        self.assertEqual(self.dut.inst2_pregs.prs1, 0)
        self.assertEqual(self.dut.inst2_pregs.prs2, 0)

        self.dut.inst1_lregs @= e
        self.dut.inst2_lregs @= f
        self.dut.sim_tick()

        self.assertEqual(self.dut.free_list, ALL_HIGH << 5)
        self.assertTrue(
            self.dut.busy_table & (ONE << 1 | ONE << 2 | ONE << 3 | ONE << 4)
        )
        # testing that logical x0 registers point to physical x0 registers
        self.assertEqual(self.dut.inst1_pregs.prs1, 0)
        self.assertEqual(self.dut.inst1_pregs.prs2, 0)
        self.assertEqual(self.dut.inst2_pregs.prs1, 0)
        self.assertEqual(self.dut.inst2_pregs.prs2, 0)

    def test_noop(self):
        # test that noop does nothing
        noop = LogicalRegs(lrd=0, lrs1=0, lrs2=0)

        self.dut.sim_eval_combinational()
        freelist = self.dut.free_list
        busytable = self.dut.busy_table
        map_table = self.dut.map_table

        for _ in range(5):
            self.dut.inst1_lregs @= noop
            self.dut.inst2_lregs @= noop
            self.dut.sim_tick()

        self.assertEqual(self.dut.free_list, freelist)
        self.assertEqual(self.dut.busy_table, busytable)
        self.assertEqual(self.dut.map_table, map_table)

    def test_reset(self):
        self.test_dest_src_rename()
        self.dut.sim_reset()
        self.assertEqual(self.dut.free_list, Bits(NUM_PHYS_REGS, -1) << 1)
        self.assertEqual(self.dut.busy_table, 0)
        self.assertEqual(self.dut.map_table, [0] * NUM_ISA_REGS)
