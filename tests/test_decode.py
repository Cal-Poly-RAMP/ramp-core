import unittest
from pymtl3 import *

from src.cl.fetch_stage import FetchPacket
from src.cl.decode import (
    ALU_LUI_COPY,
    ALU_SLL,
    BRANCH_FUNCT_UNIT,
    BRANCH_ISSUE_UNIT,
    MEM_LOAD,
    MEM_STORE,
    NA_FUNCT_UNIT,
    NA_ISSUE_UNIT,
    MicroOp,
    Decode,
    NO_OP,
    INT_ISSUE_UNIT,
    MEM_ISSUE_UNIT,
    NA_FUNCT_UNIT,
    ALU_FUNCT_UNIT,
    MEM_FUNCT_UNIT,
    NA_TYPE,
    R_TYPE,
    I_TYPE,
    S_TYPE,
    B_TYPE,
    U_TYPE,
    J_TYPE,
    CSR_TYPE,
    ALU_ADD,
    ALU_SUB,
)


class TestDecode(unittest.TestCase):
    def setUp(s) -> None:
        # runs before every test
        s.dut = Decode()
        s.dut.apply(
            DefaultPassGroup(textwave=True, linetrace=True, vcdwave="vcd/test_decode")
        )
        s.dut.sim_reset()
        s.maxDiff = None

    def tearDown(s) -> None:
        # runs after every test
        if s.dut.sim_cycle_count():
            print("final:", s.dut.line_trace())
            s.dut.print_textwave()

    def test_decode_u_r_regs_imm(s):
        # tests utype, rtype
        # proper regs, immediates, busy, forwarding
        # TODO: function to assemble instructions for working with hypothesis
        inst1 = 0x0BEEF937  # lui x18, 0xBEEF
        inst2 = 0x012909B3  # add x19, x18, x18
        fp = FetchPacket(inst1=inst1, inst2=inst2, pc=0, valid=1)
        s.dut.fetch_packet @= fp
        s.dut.sim_eval_combinational()

        exp_uop1 = MicroOp(
            optype=U_TYPE,
            inst=inst1,
            pc=0,
            valid=1,
            lrd=18,
            lrs1=s.dut.dual_uop.uop1.lrs1.uint(),  # invalid for this instr
            lrs2=s.dut.dual_uop.uop1.lrs2.uint(),  # invalid for this instr
            prd=1,
            prs1=0,
            prs2=0,
            stale=0,
            imm=0x0BEEF000,
            issue_unit=INT_ISSUE_UNIT,
            funct_unit=ALU_FUNCT_UNIT,
            funct_op=ALU_LUI_COPY,  # functional unit operation is not set yet
        )
        exp_uop2 = MicroOp(
            optype=R_TYPE,
            inst=inst2,
            pc=4,
            valid=1,
            lrd=19,
            lrs1=18,
            lrs2=18,
            prd=2,
            prs1=1,
            prs2=1,
            stale=0,
            imm=0,
            issue_unit=INT_ISSUE_UNIT,
            funct_unit=ALU_FUNCT_UNIT,
            funct_op=ALU_ADD,  # functional unit operation is not set yet
        )

        s.assertEqual(str(s.dut.dual_uop.uop1), str(exp_uop1))
        s.assertEqual(str(s.dut.dual_uop.uop2), str(exp_uop2))

    def test_decode_i_s_regs_imm(s):
        # tests itype, btype
        # proper regs, immediates
        # TODO: decoded uop components specific to load/store
        inst1 = 0x0209A903  # lw x18,   0x20(x19)
        inst2 = 0x054AA023  # sw x20,   0x40(x21)

        fp = FetchPacket(inst1=inst1, inst2=inst2, pc=8, valid=1)
        s.dut.fetch_packet @= fp
        s.dut.sim_eval_combinational()

        exp_uop1 = MicroOp(
            optype=I_TYPE,
            inst=inst1,
            pc=8,
            valid=1,
            lrd=18,
            lrs1=19,
            lrs2=s.dut.dual_uop.uop1.lrs2.uint(),  # invalid for this instr
            prd=1,
            prs1=0,
            prs2=0,
            stale=0,
            imm=0x020,
            issue_unit=MEM_ISSUE_UNIT,
            funct_unit=MEM_FUNCT_UNIT,  # functional unit is not set yet
            funct_op=s.dut.dual_uop.uop1.funct_op.uint(),  # functional unit operation is not set yet
        )
        exp_uop2 = MicroOp(
            optype=S_TYPE,
            inst=inst2,
            pc=12,
            valid=1,
            lrd=s.dut.dual_uop.uop2.lrd.uint(),  # invalid for this instr
            lrs1=21,
            lrs2=20,
            prd=0,
            prs1=0,
            prs2=0,
            stale=0,
            imm=0x040,
            issue_unit=MEM_ISSUE_UNIT,
            funct_unit=MEM_FUNCT_UNIT,  # functional unit is not set yet
            funct_op=s.dut.dual_uop.uop2.funct_op.uint(),  # functional unit operation is not set yet
        )

        s.assertEqual(str(s.dut.dual_uop.uop1), str(exp_uop1))
        s.assertEqual(str(s.dut.dual_uop.uop2), str(exp_uop2))

    def test_decode_j_b_regs_imm(s):
        # tests jtype, btype
        # proper regs, immediates
        # TODO: decoded uop components specific to jump, branch
        inst1 = 0x004000EF  # backward: jal	forward
        inst2 = 0xFF390EE3  # forward: beq	x18,	x19,	backward

        fp = FetchPacket(inst1=inst1, inst2=inst2, pc=12, valid=1)
        s.dut.fetch_packet @= fp
        s.dut.sim_eval_combinational()

        exp_uop1 = MicroOp(
            optype=J_TYPE,
            inst=inst1,
            pc=12,
            valid=1,
            lrd=1,
            lrs1=0,
            lrs2=0,
            prd=1,
            prs1=0,
            prs2=0,
            stale=0,
            imm=0x00000004,
            issue_unit=BRANCH_ISSUE_UNIT,
            funct_unit=BRANCH_FUNCT_UNIT,
            funct_op=0b00,  # functional unit operation is not set yet
        )
        exp_uop2 = MicroOp(
            optype=B_TYPE,
            inst=inst2,
            pc=16,
            valid=1,
            lrd=0,
            lrs1=18,
            lrs2=19,
            prd=0,
            prs1=0,
            prs2=0,
            stale=0,
            imm=-4,
            issue_unit=BRANCH_ISSUE_UNIT,
            funct_unit=BRANCH_FUNCT_UNIT,
            funct_op=0b00,  # functional unit operation is not set yet
        )

        s.assertEqual(str(s.dut.dual_uop.uop1), str(exp_uop1))
        s.assertEqual(str(s.dut.dual_uop.uop2), str(exp_uop2))

    def test_multiple_decode(s):
        # tests multiple decode back-to-back
        # lw x2,0x20(x1) : slli x3,x2,2
        fp1 = FetchPacket(inst1=0x0200A103, inst2=0x00211193, pc=0, valid=1)
        # slli x4,x2,1 : add x4,x4,x3
        fp2 = FetchPacket(inst1=0x00111213, inst2=0x00320233, pc=8, valid=1)
        # sw x4,0x40(x1) : noop
        fp3 = FetchPacket(inst1=0x0440A023, inst2=0x0, pc=16, valid=1)

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
            funct_op=MEM_LOAD,
        )
        uop1b = MicroOp(
            optype=I_TYPE,
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
            funct_op=ALU_SLL,
        )
        # fp2
        uop2a = MicroOp(
            optype=I_TYPE,
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
            funct_unit=ALU_FUNCT_UNIT,
            funct_op=ALU_SLL,
        )
        uop2b = MicroOp(
            optype=R_TYPE,
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
            funct_unit=ALU_FUNCT_UNIT,
            funct_op=ALU_ADD,
        )
        # fp3
        uop3a = MicroOp(
            optype=S_TYPE,
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
            funct_unit=MEM_FUNCT_UNIT,
            funct_op=MEM_STORE,
        )
        uop3b = MicroOp(
            optype=NA_TYPE,
            inst=fp3.inst2,
            pc=20,
            valid=0,
            lrd=0,
            lrs1=0,
            lrs2=0,
            prd=0,
            prs1=0,
            prs2=0,
            stale=0,
            imm=0x00000000,
            issue_unit=NA_ISSUE_UNIT,
            funct_unit=NA_FUNCT_UNIT,  # functional unit is not set yet
            funct_op=0b00,  # functional unit operation is not set yet
        )

        s.dut.fetch_packet @= fp1
        s.dut.sim_eval_combinational()
        s.assertEqual(str(s.dut.dual_uop.uop1), str(uop1a))
        s.assertEqual(str(s.dut.dual_uop.uop2), str(uop1b))

        s.dut.sim_tick()
        s.dut.fetch_packet @= fp2
        s.dut.sim_eval_combinational()
        s.assertEqual(str(s.dut.dual_uop.uop1), str(uop2a))
        s.assertEqual(str(s.dut.dual_uop.uop2), str(uop2b))

        s.dut.sim_tick()
        s.dut.fetch_packet @= fp3
        s.dut.sim_eval_combinational()
        s.assertEqual(str(s.dut.dual_uop.uop1), str(uop3a))
        s.assertEqual(str(s.dut.dual_uop.uop2), str(uop3b))

    def test_multiple_decode_reset(s):
        # tests multiple decode back-to-back
        s.test_decode_u_r_regs_imm()
        s.dut.sim_reset()
        s.test_decode_i_s_regs_imm()
        s.dut.sim_reset()
        s.test_decode_j_b_regs_imm

    def test_decode_r_type(s):
        fp = FetchPacket(inst1=0x001101B3, inst2=0x40B606B3, pc=0, valid=1)
        uop1 = MicroOp(
            optype=R_TYPE,
            inst=0x001101B3,
            pc=0,
            valid=1,
            lrd=3,
            lrs1=2,
            lrs2=1,
            prd=1,
            prs1=0,
            prs2=0,
            stale=0,
            imm=0,
            issue_unit=INT_ISSUE_UNIT,
            funct_unit=ALU_FUNCT_UNIT,
            funct_op=ALU_ADD,
            rob_idx=0,
        )
        uop2 = MicroOp(
            optype=R_TYPE,
            inst=0x40B606B3,
            pc=4,
            valid=1,
            lrd=13,
            lrs1=12,
            lrs2=11,
            prd=2,
            prs1=0,
            prs2=0,
            stale=0,
            imm=0,
            issue_unit=INT_ISSUE_UNIT,
            funct_unit=ALU_FUNCT_UNIT,
            funct_op=ALU_SUB,
            rob_idx=0,
        )
        s.dut.fetch_packet @= fp
        s.dut.sim_eval_combinational()
        s.assertEqual(str(s.dut.dual_uop.uop1), str(uop1))
        s.assertEqual(str(s.dut.dual_uop.uop2), str(uop2))
