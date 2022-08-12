from pymtl3 import *
from src.cl.register_rename import NUM_PHYS_REGS, PHYS_REG_BITWIDTH
from src.cl.ramp_core import RampCore
from src.cl.fetch_stage import FetchPacket
from pymtl3.stdlib.test_utils import config_model_with_cmdline_opts
from src.cl.decode import (
    INSTR_NOP,
    NO_OP,
    DualMicroOp,
    MicroOp,
    NA_ISSUE_UNIT,
    INT_ISSUE_UNIT,
    MEM_ISSUE_UNIT,
    NA_FUNCTIONAL_UNIT,
    ALU_FUNCT_UNIT,
    MEM_FUNCT_UNIT,
    R_TYPE,
    I_TYPE,
    S_TYPE,
    B_TYPE,
    U_TYPE,
    J_TYPE,
    CSR_TYPE,
    ALU_ADD,
    ALU_SUB,
    ALU_OR,
    ALU_AND,
    ALU_XOR,
    ALU_SRL,
    ALU_SLL,
    ALU_SRA,
    ALU_SLT,
    ALU_SLTU,
    ALU_LUI_COPY,
)


def test_system(cmdline_opts):
    # Configure the model from command line flags
    dut = RampCore()
    dut = config_model_with_cmdline_opts(dut, cmdline_opts, duts=[])
    dut.apply(DefaultPassGroup(linetrace=True, vcdwave="vcd/test_ramp_core"))
    dut.sim_reset()
    dut.fetch_stage.icache.load_file("tests/input_files/test_ramp_core1.bin")

    # 0 Configure starting state
    dut.decode.register_rename.free_list_next @= 0xFFFFFFFFFFFFFFE0
    dut.decode.register_rename.map_table[1] <<= 1
    dut.decode.register_rename.map_table[2] <<= 2
    dut.decode.register_rename.map_table[12] <<= 3
    dut.decode.register_rename.map_table[11] <<= 4
    dut.register_file.regs[1] <<= 30
    dut.register_file.regs[2] <<= 39
    dut.register_file.regs[3] <<= 450
    dut.register_file.regs[4] <<= 30

    # 1 FETCH
    dut.sim_tick()
    # inst1: add x3, x2, x1 inst2: sub x13, x12, x11
    fp = FetchPacket(inst1=0x001101B3, inst2=0x40B606B3, pc=0, valid=1)

    # Fetch | Decode
    assert dut.pr1.out == fp
    # Decode | Dispatch/Issue
    assert not dut.pr2.out
    # Dispatch/Issue | Execute
    assert not dut.pr3.out

    # 2 DECODE
    dut.sim_tick()
    uop1 = MicroOp(
        optype=R_TYPE,
        inst=0x001101B3,
        pc=0,
        valid=1,
        lrd=3,
        lrs1=2,
        lrs2=1,
        prd=5,
        prs1=2,
        prs2=1,
        stale=0,
        prs1_busy=0,
        prs2_busy=0,
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
        prd=6,
        prs1=3,
        prs2=4,
        stale=0,
        prs1_busy=0,
        prs2_busy=0,
        imm=0,
        issue_unit=INT_ISSUE_UNIT,
        funct_unit=ALU_FUNCT_UNIT,
        funct_op=ALU_SUB,
        rob_idx=0,
    )

    # Fetch | Decode
    assert dut.pr1.out == FetchPacket(inst1=0, inst2=0, pc=8, valid=1)
    # Decode | Dispatch/Issue
    assert str(dut.pr2.out.uop1) == str(uop1)
    assert dut.pr2.out.uop1 == uop1
    assert str(dut.pr2.out.uop2) == str(uop2)
    assert dut.pr2.out.uop2 == uop2
    # Dispatch/Issue | Execute
    assert not dut.pr3.out

    # 3 EXECUTE
    dut.sim_tick()
    uop2.rob_idx @= 1
    # Fetch | Decode
    assert dut.pr1.out == FetchPacket(inst1=0, inst2=0, pc=16, valid=1)
    # Decode | Dispatch/Issue
    assert not dut.pr2.out.uop1.valid and not dut.pr2.out.uop2.valid
    # Dispatch/Issue | Execute
    assert not dut.pr3.out

    dut.sim_tick()
    # Fetch | Decode
    assert dut.pr1.out == FetchPacket(inst1=0, inst2=0, pc=24, valid=1)
    # Decode | Dispatch/Issue
    assert not dut.pr2.out.uop1.valid and not dut.pr2.out.uop2.valid
    # Dispatch/Issue | Execute
    assert not dut.pr3.out

    dut.sim_tick()
    # Fetch | Decode
    assert dut.pr1.out == FetchPacket(inst1=0, inst2=0, pc=32, valid=1)
    # Decode | Dispatch/Issue
    assert not dut.pr2.out.uop1.valid and not dut.pr2.out.uop2.valid
    # Dispatch/Issue | Execute
    assert dut.pr3.out == uop1

    dut.sim_tick()
    # Fetch | Decode
    assert dut.pr1.out == FetchPacket(inst1=0, inst2=0, pc=40, valid=1)
    # Decode | Dispatch/Issue
    assert not dut.pr2.out.uop1.valid and not dut.pr2.out.uop2.valid
    # Dispatch/Issue | Execute
    assert dut.pr3.out == uop2
    # Commit
    assert dut.reorder_buffer.commit_out.uop1_entry.data == 69

    # 4 WRITEBACK
    dut.sim_tick()
    # Fetch | Decode
    assert dut.pr1.out == FetchPacket(inst1=0, inst2=0, pc=48, valid=1)
    # Decode | Dispatch/Issue
    assert not dut.pr2.out.uop1.valid and not dut.pr2.out.uop2.valid
    # Dispatch/Issue | Execute
    assert dut.pr3.out == uop2
    # Commit
    assert dut.reorder_buffer.commit_out.uop2_entry.data == 420


    dut.sim_tick()


    # Cleanup
    assert False