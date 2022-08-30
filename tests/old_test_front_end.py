import unittest
from pymtl3 import DefaultPassGroup, concat
from src.cl.front_end import FrontEnd

from src.common.interfaces import MicroOp, FetchPacket
from src.common.consts import (
    INT_ISSUE_UNIT,
    MEM_ISSUE_UNIT,
    ALU_FUNCT_UNIT,
    MEM_FUNCT_UNIT,
    R_TYPE,
    S_TYPE,
    I_TYPE,
    NA_TYPE,
)


class TestFrontEnd(unittest.TestCase):
    def setUp(s) -> None:
        # runs before every test
        s.dut = FrontEnd()
        s.dut.apply(
            DefaultPassGroup(
                textwave=True, linetrace=True, vcdwave="vcd/test_front_end"
            )
        )
        s.maxDiff = None
        s.dut.elaborate()
        s.dut.sim_reset()

    def tearDown(s) -> None:
        # runs after every test
        if s.dut.sim_cycle_count():
            print("final:", s.dut.line_trace())
            s.dut.print_textwave()

    def test_multiple_fetch(s):
        # tests multiple decode back-to-back
        # lw x2,0x20(x1) : slli x3,x2,2
        fp1 = FetchPacket(inst1=0x0200A103, inst2=0x00211193, pc=0, valid=1)
        # slli x4,x2,1 : add x4,x4,x3
        fp2 = FetchPacket(inst1=0x00111213, inst2=0x00320233, pc=8, valid=1)
        # sw x4,0x40(x1) : noop
        fp3 = FetchPacket(inst1=0x0440A023, inst2=0x0, pc=12, valid=1)

        # loading the instructions into memory
        s.dut.fetch_stage.icache.write_word(0, concat(fp1.inst1, fp1.inst2))
        s.dut.fetch_stage.icache.write_word(8, concat(fp2.inst1, fp2.inst2))
        s.dut.fetch_stage.icache.write_word(16, concat(fp3.inst1, fp3.inst2))

        # fp1
        uop1a = MicroOp(
            optype=I_TYPE,
            inst=fp1.inst1,
            pc=0,
            valid=1,
            lrd=2,
            lrs1=1,
            lrs2=0,
            prd=1,
            prs1=0,
            prs2=0,
            stale=0,
            imm=0x00000020,
            issue_unit=MEM_ISSUE_UNIT,
            funct_unit=MEM_FUNCT_UNIT,
            funct_op=0b00,  # functional unit operation is not set yet
        )
        uop1b = MicroOp(
            optype=I_TYPE,  # not set yet
            inst=fp1.inst2,
            pc=4,
            valid=1,
            lrd=3,
            lrs1=2,
            lrs2=0,
            prd=2,
            prs1=1,
            prs2=0,
            stale=0,
            imm=0x00000002,
            issue_unit=INT_ISSUE_UNIT,
            funct_unit=ALU_FUNCT_UNIT,
            funct_op=0b00,  # functional unit operation is not set yet
        )
        # fp2
        uop2a = MicroOp(
            optype=I_TYPE,  # not set yet
            inst=fp2.inst1,
            pc=8,
            valid=1,
            lrd=4,
            lrs1=2,
            lrs2=0,
            prd=3,
            prs1=1,
            prs2=0,
            stale=0,
            imm=0x00000001,
            issue_unit=INT_ISSUE_UNIT,
            funct_unit=ALU_FUNCT_UNIT,  # functional unit is not set yet
            funct_op=0b00,  # functional unit operation is not set yet
        )
        uop2b = MicroOp(
            optype=R_TYPE,  # not set yet
            inst=fp2.inst2,
            pc=12,
            valid=1,
            lrd=4,
            lrs1=4,
            lrs2=3,
            prd=4,
            prs1=3,
            prs2=2,
            stale=3,
            imm=0x00000000,
            issue_unit=INT_ISSUE_UNIT,
            funct_unit=ALU_FUNCT_UNIT,  # functional unit is not set yet
            funct_op=0b00,  # functional unit operation is not set yet
        )
        # fp3
        uop3a = MicroOp(
            optype=S_TYPE,  # not set yet
            inst=fp3.inst1,
            pc=16,
            valid=1,
            lrd=0,
            lrs1=1,
            lrs2=4,
            prd=0,
            prs1=0,
            prs2=4,
            stale=0,
            imm=0x00000040,
            issue_unit=MEM_ISSUE_UNIT,
            funct_unit=MEM_FUNCT_UNIT,  # functional unit is not set yet
            funct_op=0b00,  # functional unit operation is not set yet
        )
        uop3b = MicroOp(
            optype=NA_TYPE,
            inst=fp3.inst2,
            pc=20,
            valid=1,
            lrd=0,
            lrs1=0,
            lrs2=0,
            prd=0,
            prs1=0,
            prs2=0,
            stale=0,
            imm=0x00000000,
            issue_unit=INT_ISSUE_UNIT,
            funct_unit=ALU_FUNCT_UNIT,  # functional unit is not set yet
            funct_op=0b00,  # functional unit operation is not set yet
        )

        s.dut.sim_tick()  # fetch 1,2 -> reg 1,2 -> decode
        s.assertEqual(str(s.dut.dual_uop.uop1), str(uop1a))
        s.assertEqual(str(s.dut.dual_uop.uop2), str(uop1b))

        s.dut.sim_tick()  # fetch 5,6 -> reg 3,4 -> decode
        s.assertEqual(str(s.dut.dual_uop.uop1), str(uop2a))
        s.assertEqual(str(s.dut.dual_uop.uop2), str(uop2b))

        s.dut.sim_tick()  # fetch 7,8 -> reg 5,6 -> decode
        s.assertEqual(str(s.dut.dual_uop.uop1), str(uop3a))
        s.assertEqual(str(s.dut.dual_uop.uop2), str(uop3b))
