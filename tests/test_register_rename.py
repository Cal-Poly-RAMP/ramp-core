import unittest
from pymtl3 import *

from src.cl.register_rename import RegisterRename, LogicalRegs, PhysicalRegs


"""
    # interface
    s.inst1_lregs = InPort(LogicalRegs)
    s.inst2_lregs = InPort(LogicalRegs)
    s.inst2_pregs = OutPort(PhysicalRegs)
    s.inst1_pregs = OutPort(PhysicalRegs)

    s.free_list = OutPort(PhysicalRegs)
    s.busy_table = OutPort(PhysicalRegs)

    # map tables
    s.inst1_map_table = [Bits(PHYS_REG_BITWIDTH, 0)] * NUM_ISA_REGS
    s.inst2_map_table = [Bits(PHYS_REG_BITWIDTH, 0)] * NUM_ISA_REGS

    # internal freelist
    s._free_list = Bits(NUM_PHYS_REGS, 1)  # implemented as bit vector 1 -> free

    # internal busy table
    s._busy_table = [Bits(NUM_PHYS_REGS, 0)]
"""


class TestRegisterRename(unittest.TestCase):
    def setUp(self):
        self.dut = RegisterRename()
        self.dut.apply(DefaultPassGroup())
        self.dut.sim_reset()

    def test_simple_dest_rename(self):
        # making sure multiple renamed registers are not equal
        self.dut.sim_reset()

        inst1_lregs = LogicalRegs(lrd=18, lrs1=0, lrs2=0)
        inst2_lregs = LogicalRegs(lrd=19, lrs1=0, lrs2=0)
        self.dut.inst1_lregs @= inst1_lregs
        self.dut.inst2_lregs @= inst2_lregs

        self.dut.sim_tick()

        assigned_regs = []
        for w in [
            self.dut.inst2_pregs.prd,
            self.dut.inst1_pregs.prd,
        ]:
            self.assertNotIn(w.uint(), assigned_regs)
            assigned_regs.append(w.uint())

    def test_dest_src_rename(self):
        # making sure that src registers point to renamed dest registers from previous instructions
        d = self.dut

        inst1_lregs = LogicalRegs(lrd=18, lrs1=0, lrs2=0)
        inst2_lregs = LogicalRegs(lrd=19, lrs1=0, lrs2=0)
        self.dut.inst1_lregs @= inst1_lregs
        self.dut.inst2_lregs @= inst2_lregs
        d.sim_tick()

        prd1_1 = d.inst1_pregs.prd.uint()
        prd2_1 = d.inst2_pregs.prd.uint()

        inst1_lregs = LogicalRegs(lrd=20, lrs1=18, lrs2=19)
        inst2_lregs = LogicalRegs(lrd=21, lrs1=19, lrs2=18)
        self.dut.inst1_lregs @= inst1_lregs
        self.dut.inst2_lregs @= inst2_lregs
        d.sim_tick()

        print(d.line_trace())

        self.assertEqual(prd1_1, d.inst1_pregs.prs1.uint())
        self.assertEqual(prd1_1, d.inst2_pregs.prs2.uint())

        self.assertEqual(prd2_1, d.inst1_pregs.prs2.uint())
        self.assertEqual(prd2_1, d.inst2_pregs.prs1.uint())

    def test_dest_src_rename(self):
        # making sure that src registers point to renamed dest registers from previous instructions
        d = self.dut

        inst1_lregs = LogicalRegs(lrd=18, lrs1=0, lrs2=0)
        inst2_lregs = LogicalRegs(lrd=19, lrs1=0, lrs2=0)
        self.dut.inst1_lregs @= inst1_lregs
        self.dut.inst2_lregs @= inst2_lregs
        d.sim_tick()

        prd1_1 = d.inst1_pregs.prd.uint()
        prd2_1 = d.inst2_pregs.prd.uint()

        inst1_lregs = LogicalRegs(lrd=20, lrs1=18, lrs2=19)
        inst2_lregs = LogicalRegs(lrd=21, lrs1=19, lrs2=18)
        self.dut.inst1_lregs @= inst1_lregs
        self.dut.inst2_lregs @= inst2_lregs
        d.sim_tick()

        print(d.line_trace())

        self.assertEqual(prd1_1, d.inst1_pregs.prs1.uint())
        self.assertEqual(prd1_1, d.inst2_pregs.prs2.uint())

        self.assertEqual(prd2_1, d.inst1_pregs.prs2.uint())
        self.assertEqual(prd2_1, d.inst2_pregs.prs1.uint())
