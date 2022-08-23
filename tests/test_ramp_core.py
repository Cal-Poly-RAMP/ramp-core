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
    NA_FUNCT_UNIT,
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


def test_system_dual_rtype(cmdline_opts):
    # Configure the model from command line flags
    dut = RampCore()
    dut = config_model_with_cmdline_opts(dut, cmdline_opts, duts=[])
    dut.apply(DefaultPassGroup(linetrace=True, vcdwave="vcd/test_ramp_core1"))
    dut.sim_reset()
    # add x3, x2, x1
    # sub x13, x12, x11
    dut.fetch_stage.icache.load_file("tests/input_files/test_system1.bin")

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
    fp = FetchPacket(inst1=0x001101B3, inst2=0x40B606B3, pc=0, valid=1)

    # Fetch | Decode
    assert dut.pr1.out == fp
    # Decode | Dispatch/Issue
    assert not dut.pr2.out
    # Dispatch/Issue | Execute
    # assert not dut.pr3.out
    assert not dut.int_issue_queue.uop_out

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
        imm=0,
        issue_unit=INT_ISSUE_UNIT,
        funct_unit=ALU_FUNCT_UNIT,
        funct_op=ALU_ADD,
        rob_idx=0,
        mem_q_idx=0,
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
        imm=0,
        issue_unit=INT_ISSUE_UNIT,
        funct_unit=ALU_FUNCT_UNIT,
        funct_op=ALU_SUB,
        rob_idx=0,
        mem_q_idx=0,
    )

    # Fetch | Decode
    assert dut.pr1.out == FetchPacket(inst1=0, inst2=0, pc=8, valid=1)
    # Decode | Dispatch/Issue
    assert dut.pr2.out.uop1 == uop1
    assert dut.pr2.out.uop2 == uop2
    # Dispatch/Issue | Execute
    # assert not dut.pr3.out
    assert not dut.int_issue_queue.uop_out

    # 3 EXECUTE
    dut.sim_tick()
    uop2.rob_idx @= 1
    # Fetch | Decode
    assert dut.pr1.out == FetchPacket(inst1=0, inst2=0, pc=16, valid=1)
    # Decode | Dispatch/Issue
    assert not dut.pr2.out.uop1.valid and not dut.pr2.out.uop2.valid
    # Dispatch/Issue | Execute
    # assert not dut.pr3.out
    assert dut.int_issue_queue.uop_out == uop1

    # dut.sim_tick()
    # # Fetch | Decode
    # assert dut.pr1.out == FetchPacket(inst1=0, inst2=0, pc=24, valid=1)
    # # Decode | Dispatch/Issue
    # assert not dut.pr2.out.uop1.valid and not dut.pr2.out.uop2.valid
    # # Dispatch/Issue | Execute
    # # assert dut.pr3.out == uop1
    # assert dut.int_issue_queue.uop_out == uop1

    # 4 COMMIT
    dut.sim_tick()
    # Fetch | Decode
    assert dut.pr1.out == FetchPacket(inst1=0, inst2=0, pc=24, valid=1)
    # Decode | Dispatch/Issue
    assert not dut.pr2.out.uop1.valid and not dut.pr2.out.uop2.valid
    # Dispatch/Issue | Execute
    # assert dut.pr3.out == uop2
    assert dut.int_issue_queue.uop_out == uop2
    # Commit
    assert dut.reorder_buffer.commit_out.uop1_entry.data == 69

    # 5 WRITEBACK
    dut.sim_tick()
    # Fetch | Decode
    assert dut.pr1.out == FetchPacket(inst1=0, inst2=0, pc=32, valid=1)
    # Decode | Dispatch/Issue
    assert not dut.pr2.out.uop1.valid and not dut.pr2.out.uop2.valid
    # Dispatch/Issue | Execute
    # assert not dut.pr3.out
    assert not dut.int_issue_queue.uop_out
    # Commit
    assert dut.reorder_buffer.commit_out.uop2_entry.data == 420
    # Writeback
    assert dut.register_file.regs[5] == 69

    dut.sim_tick()
    # Fetch | Decode
    assert dut.pr1.out == FetchPacket(inst1=0, inst2=0, pc=40, valid=1)
    # Decode | Dispatch/Issue
    assert not dut.pr2.out.uop1.valid and not dut.pr2.out.uop2.valid
    # Dispatch/Issue | Execute
    # assert not dut.pr3.out
    assert not dut.int_issue_queue.uop_out
    # Commit
    assert not dut.reorder_buffer.commit_out.uop2_entry.data
    # Writeback
    assert dut.register_file.regs[5] == 69
    assert dut.register_file.regs[6] == 420

    # 7 cycles (reset makes 9)


def test_system_iu_type(cmdline_opts):
    # lui x1, 0x000dead0
    # addi x2, x1, 0x000000af
    dut = RampCore()
    dut = config_model_with_cmdline_opts(dut, cmdline_opts, duts=[])
    dut.apply(DefaultPassGroup(linetrace=True, vcdwave="vcd/test_ramp_core2"))
    dut.sim_reset()

    # Load Program
    dut.fetch_stage.icache.load_file("tests/input_files/test_system2.bin")

    prd = dut.decode.register_rename.map_table[2]
    for _ in range(8):
        dut.sim_tick()
    assert dut.register_file.regs[prd] == 0x0DEAD0AF


def test_system_multiple(cmdline_opts):
    # addi	t0,	x0,	6   0x00600293
    # slli	t1,	t0,	3   0x00329313
    # slli	t2,	t0,	1   0x00129393
    # add	t0,	t1,	t2  0x007302b3

    dut = RampCore()
    dut = config_model_with_cmdline_opts(dut, cmdline_opts, duts=[])
    dut.apply(DefaultPassGroup(linetrace=True, vcdwave="vcd/test_ramp_core3"))
    dut.sim_reset()

    # Load Program
    dut.fetch_stage.icache.load_file("tests/input_files/test_system3.bin")

    prd = dut.decode.register_rename.map_table[5]
    for _ in range(12):
        dut.sim_tick()

    assert dut.register_file.regs[prd] == 60


def test_system_multiple2(cmdline_opts):
    # Program to multiply by 50
    # 6 << 7 + c << 5 + 6 << 2) >> 1
    # ori	t0,	x0,	6
    # andi	t1,	t0,	2
    # addi	t2,	x0,	5
    # addi	t3,	x0,	7

    # sll	t1,	t0,	t1
    # sll	t2,	t0, 	t2
    # sll	t3,	t0,	t3

    # sub	t0,	t3,	t2
    # add	t0,	t1,	t0

    # srai	t0,	t0,	1

    dut = RampCore()
    dut = config_model_with_cmdline_opts(dut, cmdline_opts, duts=[])
    dut.apply(DefaultPassGroup(linetrace=True, vcdwave="vcd/test_ramp_core4"))
    dut.sim_reset()

    # Load Program
    dut.fetch_stage.icache.load_file("tests/input_files/test_system4.bin")

    prd = dut.decode.register_rename.map_table[5]
    for _ in range(22):
        dut.sim_tick()
    assert dut.register_file.regs[prd] == 300


def test_system5(cmdline_opts):
    # Program to multiply by 314

    dut = RampCore()
    dut = config_model_with_cmdline_opts(dut, cmdline_opts, duts=[])
    dut.apply(DefaultPassGroup(linetrace=True, vcdwave="vcd/test_ramp_core5"))
    dut.sim_reset()

    # Load Program
    dut.fetch_stage.icache.load_file("tests/input_files/test_system5.bin")

    prd = dut.decode.register_rename.map_table[5]
    for _ in range(17):
        dut.sim_tick()
    assert dut.register_file.regs[prd] == 1884
