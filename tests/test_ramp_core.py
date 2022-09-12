# https://pymtl3.readthedocs.io/en/latest/ref/passes-import-intro.html
import os
from pymtl3 import DefaultPassGroup
from pymtl3.stdlib.test_utils import config_model_with_cmdline_opts
from pymtl3.passes.backends.verilog import VerilogVerilatorImportPass
from pymtl3.passes.backends.verilog.translation.VerilogTranslationPass import VerilogTranslationPass

from src.cl.ramp_core import RampCore
from src.fl.util import get_mem

from src.common.interfaces import MicroOp, FetchPacket
from src.common.consts import (
    INT_ISSUE_UNIT,
    ALU_FUNCT_UNIT,
    R_TYPE,
    ALU_ADD,
    ALU_SUB,
    NUM_PHYS_REGS,
    ICACHE_SIZE
)

LNTRC = True


# def test_system_dual_rtype(cmdline_opts):
#     # Configure the model from command line flags
#     # add x3, x2, x1
#     # sub x13, x12, x11

#     # short circuiting verilog tests, no MMIO
#     if cmdline_opts['test_verilog']:
#         print("Skipping non-verilog test")
#         return

#     filename = "tests/input_files/test_system1.bin"
#     dut = RampCore(data=get_mem(filename, ICACHE_SIZE))

#     dut = config_model_with_cmdline_opts(dut, cmdline_opts, duts=[])
#     dut.apply(DefaultPassGroup(linetrace=LNTRC, vcdwave="vcd/test_ramp_core1"))
#     dut.sim_reset()

#     # 0 Configure starting state
#     dut.decode.register_rename.free_list_next @= 0xFFFFFFFFFFFFFFE0
#     dut.decode.register_rename.map_table[1] <<= 1
#     dut.decode.register_rename.map_table[2] <<= 2
#     dut.decode.register_rename.map_table[12] <<= 3
#     dut.decode.register_rename.map_table[11] <<= 4
#     dut.register_file.regs[1] <<= 30
#     dut.register_file.regs[2] <<= 39
#     dut.register_file.regs[3] <<= 450
#     dut.register_file.regs[4] <<= 30

#     # 1 FETCH
#     dut.sim_tick()
#     fp = FetchPacket(inst1=0x001101B3, inst2=0x40B606B3, pc=0, valid=1)

#     # Fetch | Decode
#     assert dut.pr1.out == fp
#     # Decode | Dispatch/Issue
#     assert not dut.pr2.out
#     # Dispatch/Issue | Execute
#     # assert not dut.pr3.out
#     assert not dut.int_issue_queue.uop_out

#     # 2 DECODE
#     dut.sim_tick()
#     uop1 = MicroOp(
#         optype=R_TYPE,
#         inst=0x001101B3,
#         pc=0,
#         valid=1,
#         lrd=3,
#         lrs1=2,
#         lrs2=1,
#         prd=dut.pr2.out.uop1.prd,
#         prs1=dut.pr2.out.uop1.prs1,
#         prs2=dut.pr2.out.uop1.prs2,
#         stale=0,
#         imm=0,
#         issue_unit=INT_ISSUE_UNIT,
#         funct_unit=ALU_FUNCT_UNIT,
#         funct_op=ALU_ADD,
#         rob_idx=0,
#         mem_q_idx=0,
#     )
#     uop2 = MicroOp(
#         optype=R_TYPE,
#         inst=0x40B606B3,
#         pc=4,
#         valid=1,
#         lrd= 13,
#         lrs1=12,
#         lrs2=11,
#         prd=dut.pr2.out.uop2.prd,
#         prs1=dut.pr2.out.uop2.prs1,
#         prs2=dut.pr2.out.uop2.prs2,
#         stale=0,
#         imm=0,
#         issue_unit=INT_ISSUE_UNIT,
#         funct_unit=ALU_FUNCT_UNIT,
#         funct_op=ALU_SUB,
#         rob_idx=0,
#         mem_q_idx=0,
#     )

#     # Fetch | Decode
#     assert dut.pr1.out == FetchPacket(inst1=0, inst2=0, pc=8, valid=1)
#     # Decode | Dispatch/Issue
#     assert dut.pr2.out.uop1 == uop1
#     assert dut.pr2.out.uop2 == uop2
#     assert dut.pr2.out.uop1.prd != dut.pr2.out.uop2.prd
#     # Dispatch/Issue | Execute
#     # assert not dut.pr3.out
#     assert not dut.int_issue_queue.uop_out

#     # 3 EXECUTE
#     dut.sim_tick()
#     uop2.rob_idx @= 1
#     # Fetch | Decode
#     assert dut.pr1.out == FetchPacket(inst1=0, inst2=0, pc=16, valid=1)
#     # Decode | Dispatch/Issue
#     assert not dut.pr2.out.uop1.valid and not dut.pr2.out.uop2.valid
#     # Dispatch/Issue | Execute
#     # assert not dut.pr3.out
#     assert dut.int_issue_queue.uop_out == uop1

#     # dut.sim_tick()
#     # # Fetch | Decode
#     # assert dut.pr1.out == FetchPacket(inst1=0, inst2=0, pc=24, valid=1)
#     # # Decode | Dispatch/Issue
#     # assert not dut.pr2.out.uop1.valid and not dut.pr2.out.uop2.valid
#     # # Dispatch/Issue | Execute
#     # # assert dut.pr3.out == uop1
#     # assert dut.int_issue_queue.uop_out == uop1

#     # 4 COMMIT
#     dut.sim_tick()
#     # Fetch | Decode
#     assert dut.pr1.out == FetchPacket(inst1=0, inst2=0, pc=24, valid=1)
#     # Decode | Dispatch/Issue
#     assert not dut.pr2.out.uop1.valid and not dut.pr2.out.uop2.valid
#     # Dispatch/Issue | Execute
#     # assert dut.pr3.out == uop2
#     assert dut.int_issue_queue.uop_out == uop2
#     # Commit
#     assert dut.reorder_buffer.commit_out.uop1_entry.data == 69

#     # 5 WRITEBACK
#     dut.sim_tick()
#     # Fetch | Decode
#     assert dut.pr1.out == FetchPacket(inst1=0, inst2=0, pc=32, valid=1)
#     # Decode | Dispatch/Issue
#     assert not dut.pr2.out.uop1.valid and not dut.pr2.out.uop2.valid
#     # Dispatch/Issue | Execute
#     # assert not dut.pr3.out
#     assert not dut.int_issue_queue.uop_out
#     # Commit
#     assert dut.reorder_buffer.commit_out.uop2_entry.data == 420
#     # Writeback
#     assert dut.register_file.regs[5] == 69

#     dut.sim_tick()
#     # Fetch | Decode
#     assert dut.pr1.out == FetchPacket(inst1=0, inst2=0, pc=40, valid=1)
#     # Decode | Dispatch/Issue
#     assert not dut.pr2.out.uop1.valid and not dut.pr2.out.uop2.valid
#     # Dispatch/Issue | Execute
#     # assert not dut.pr3.out
#     assert not dut.int_issue_queue.uop_out
#     # Commit
#     assert not dut.reorder_buffer.commit_out.uop2_entry.data
#     # Writeback
#     assert dut.register_file.regs[5] == 69
#     assert dut.register_file.regs[6] == 420

#     # 7 cycles (reset makes 9)


def test_system_iu_type(cmdline_opts):
    # lui x1, 0x000dead0
    # addi x2, x1, 0x000000af

    # short circuiting verilog tests, no MMIO
    if cmdline_opts['test_verilog']:
        print("Skipping non-verilog test")
        return

    filename = "tests/input_files/test_system2.bin"
    dut = RampCore(data=get_mem(filename, ICACHE_SIZE))

    dut = config_model_with_cmdline_opts(dut, cmdline_opts, duts=[])
    dut.apply(DefaultPassGroup(linetrace=LNTRC, vcdwave="vcd/test_ramp_core2"))
    dut.sim_reset()

    for _ in range(8):
        dut.sim_tick()
    prd = dut.decode.register_rename.map_table[2]
    assert dut.register_file.regs[prd] == 0x0DEAD0AF


def test_system_multiple(cmdline_opts):
    # addi	t0,	x0,	6   0x00600293
    # slli	t1,	t0,	3   0x00329313
    # slli	t2,	t0,	1   0x00129393
    # add	t0,	t1,	t2  0x007302b3

    # short circuiting verilog tests, no MMIO
    if cmdline_opts['test_verilog']:
        print("Skipping non-verilog test")
        return

    filename = "tests/input_files/test_system3.bin"
    dut = RampCore(data=get_mem(filename, ICACHE_SIZE))

    dut = config_model_with_cmdline_opts(dut, cmdline_opts, duts=[])
    dut.apply(DefaultPassGroup(linetrace=LNTRC, vcdwave="vcd/test_ramp_core3"))
    dut.sim_reset()

    for _ in range(12):
        dut.sim_tick()

    prd = dut.decode.register_rename.map_table[5]
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

    # short circuiting verilog tests, no MMIO
    if cmdline_opts['test_verilog']:
        print("Skipping non-verilog test")
        return

    filename = "tests/input_files/test_system4.bin"
    dut = RampCore(data=get_mem(filename, ICACHE_SIZE))

    dut = config_model_with_cmdline_opts(dut, cmdline_opts, duts=[])
    dut.apply(DefaultPassGroup(linetrace=LNTRC, vcdwave="vcd/test_ramp_core4"))
    dut.sim_reset()

    for _ in range(22):
        dut.sim_tick()
    prd = dut.decode.register_rename.map_table[5]
    assert dut.register_file.regs[prd] == 300


def test_system5(cmdline_opts):
    # Program to multiply by 314

    # short circuiting verilog tests, no MMIO
    if cmdline_opts['test_verilog']:
        print("Skipping non-verilog test")
        return

    filename = "tests/input_files/test_system5.bin"
    dut = RampCore(data=get_mem(filename, ICACHE_SIZE))

    dut = config_model_with_cmdline_opts(dut, cmdline_opts, duts=[])
    dut.apply(DefaultPassGroup(linetrace=LNTRC, vcdwave="vcd/test_ramp_core5"))
    dut.sim_reset()

    for _ in range(17):
        dut.sim_tick()
    prd = dut.decode.register_rename.map_table[5]
    assert dut.register_file.regs[prd] == 1884


def test_store(cmdline_opts):
    # Stores the number 42 to memory

    # short circuiting verilog tests, no MMIO
    if cmdline_opts['test_verilog']:
        print("Skipping non-verilog test")
        return

    filename = "tests/input_files/test_store.bin"
    dut = RampCore(data=get_mem(filename, ICACHE_SIZE))

    dut = config_model_with_cmdline_opts(dut, cmdline_opts, duts=[])
    dut.apply(DefaultPassGroup(linetrace=LNTRC, vcdwave="vcd/test_ramp_core_store"))
    dut.sim_reset()

    for _ in range(10):
        dut.sim_tick()
    prd = dut.decode.register_rename.map_table[1]
    assert dut.register_file.regs[prd] == 42
    assert dut.memory_unit.dram.mem[0] == 42


def test_load(cmdline_opts):
    # reads 0xdeadbeef from memory

    # short circuiting verilog tests, no MMIO
    if cmdline_opts['test_verilog']:
        print("Skipping non-verilog test")
        return

    filename = "tests/input_files/test_load.bin"
    dut = RampCore(data=get_mem(filename, ICACHE_SIZE))

    dut = config_model_with_cmdline_opts(dut, cmdline_opts, duts=[])
    dut.apply(DefaultPassGroup(linetrace=LNTRC, vcdwave="vcd/test_ramp_core_load"))
    dut.sim_reset()

    # load program
    dut.memory_unit.dram.mem[2] <<= 0xDEADBEEF

    for _ in range(10):
        dut.sim_tick()
    pr1 = dut.decode.register_rename.map_table[1]
    pr2 = dut.decode.register_rename.map_table[2]
    assert dut.register_file.regs[pr1] == 4
    assert dut.register_file.regs[pr2] == 0xDEADBEEF


def test_load_store(cmdline_opts):
    # Stores the number 42 to memory, then loads it back into registers and adds

    # short circuiting verilog tests, no MMIO
    if cmdline_opts['test_verilog']:
        print("Skipping non-verilog test")
        return

    filename = "tests/input_files/test_load_store.bin"
    dut = RampCore(data=get_mem(filename, ICACHE_SIZE))

    dut = config_model_with_cmdline_opts(dut, cmdline_opts, duts=[])
    dut.apply(DefaultPassGroup(linetrace=LNTRC, vcdwave="vcd/test_ramp_core_load_store"))
    dut.sim_reset()

    for _ in range(16):
        dut.sim_tick()

    pr1 = dut.decode.register_rename.map_table[1]
    pr2 = dut.decode.register_rename.map_table[2]
    pr3 = dut.decode.register_rename.map_table[3]
    pr4 = dut.decode.register_rename.map_table[4]
    assert dut.register_file.regs[pr1] == 8
    assert dut.register_file.regs[pr2] == 42
    assert dut.register_file.regs[pr3] == 42
    assert dut.register_file.regs[pr4] == 84
    assert dut.memory_unit.dram.mem[1] == 42

def test_ls_subwords(cmdline_opts):
    # tests lb, lh, lbu, lhu, sb, sh

    # short circuiting verilog tests, no MMIO
    if cmdline_opts['test_verilog']:
        print("Skipping non-verilog test")
        return

    filename = "tests/input_files/test_ls_subwords.bin"
    dut = RampCore(data=get_mem(filename, ICACHE_SIZE))

    dut = config_model_with_cmdline_opts(dut, cmdline_opts, duts=[])
    dut.apply(
        DefaultPassGroup(linetrace=LNTRC, vcdwave="vcd/test_ramp_core_ls_subwords")
    )
    dut.sim_reset()

    for i in range(50):
        dut.sim_tick()
        if i > 7 and dut.memory_unit.ls_queue.empty:
            dut.sim_tick()
            dut.sim_tick()
            dut.sim_tick()
            dut.sim_tick()
            dut.sim_tick()
            break

    lr_to_pr = [dut.decode.register_rename.map_table[i] for i in range(0, 9)]
    assert dut.register_file.regs[lr_to_pr[0]] == 0x00000000
    assert dut.register_file.regs[lr_to_pr[1]] == 0xDEADBEEF
    assert dut.register_file.regs[lr_to_pr[3]] == 0xFFFFFFEF
    assert dut.register_file.regs[lr_to_pr[4]] == 0xFFFFBEEF
    assert dut.register_file.regs[lr_to_pr[5]] == 0xDEADBEEF
    assert dut.register_file.regs[lr_to_pr[6]] == 0x000000EF
    assert dut.register_file.regs[lr_to_pr[7]] == 0x0000BEEF

    assert dut.memory_unit.dram.mem[0] == 0x000000EF
    assert dut.memory_unit.dram.mem[1] == 0x0000BEEF
    assert dut.memory_unit.dram.mem[2] == 0xDEADBEEF

def test_bge(cmdline_opts):
    # test always take bge without worrying about register renaming

    # short circuiting verilog tests, no MMIO
    if cmdline_opts['test_verilog']:
        print("Skipping non-verilog test")
        return

    filename = "tests/input_files/test_bge.bin"

    dut = RampCore(data=get_mem(filename, ICACHE_SIZE))

    dut = config_model_with_cmdline_opts(dut, cmdline_opts, duts=[])
    dut.apply(DefaultPassGroup(linetrace=LNTRC, vcdwave="vcd/test_ramp_core_bge"))
    dut.sim_reset()

    for x in range(100):
        dut.sim_tick()

    mem = dut.memory_unit.dram.mem
    for i in range(2, len(mem)):
        if mem[i] == 0:
            assert i > 5, "Fibonacci sequence too short"
            break
        assert mem[i] == mem[i - 1] + mem[i-2]

def test_jal(cmdline_opts):
    # test always take unconditional jump without worrying about register renaming

    # short circuiting verilog tests, no MMIO
    if cmdline_opts['test_verilog']:
        print("Skipping non-verilog test")
        return

    filename = "tests/input_files/test_jal.bin"
    dut = RampCore(data=get_mem(filename, ICACHE_SIZE))

    dut = config_model_with_cmdline_opts(dut, cmdline_opts, duts=[])
    dut.apply(DefaultPassGroup(linetrace=LNTRC, vcdwave="vcd/test_ramp_core_jal"))
    dut.sim_reset()

    for x in range(100):
        dut.sim_tick()

    mem = dut.memory_unit.dram.mem
    for i in range(2, len(mem)):
        if mem[i] == 0:
            assert i > 5, "Fibonacci sequence too short"
            break
        assert mem[i] == mem[i - 1] + mem[i-2]

        # # checking the linked register
        # pr1 = dut.decode.register_rename.map_table[lr1]
        # assert dut.register_file.regs[pr1] == 18

def test_beq(cmdline_opts):
    # test beq take half the time, don't worry about caching register renaming

    # short circuiting verilog tests, no MMIO
    if cmdline_opts['test_verilog']:
        print("Skipping non-verilog test")
        return

    filename = "tests/input_files/test_beq.bin"
    dut = RampCore(data=get_mem(filename, ICACHE_SIZE))

    # dut.set_metadata(VerilogVerilatorImportPass.vl_mk_dir, "obj_dir_RampCore")
    # dut.set_metadata(VerilogTranslationPass.explicit_module_name, "RampCore")

    dut = config_model_with_cmdline_opts(dut, cmdline_opts, duts=[])

    dut.apply(DefaultPassGroup(linetrace=LNTRC, vcdwave="vcd/test_ramp_core_beq"))
    dut.sim_reset()

    # running program
    for x in range(30):
        dut.sim_tick()

    odd_sum_lreg = 6
    even_sum_lreg = 7
    odd_sum_preg = dut.decode.register_rename.map_table[odd_sum_lreg]
    even_sum_preg = dut.decode.register_rename.map_table[even_sum_lreg]
    assert dut.register_file.regs[odd_sum_preg] == 25
    assert dut.register_file.regs[even_sum_preg] == 30

# VERILOG TESTS (using MMIO)

def test_bge_verilog(cmdline_opts):
    # test always take bge without worrying about register renaming
    # Using MMIO
    filename = "tests/input_files/test_bge_verilog.bin"

    dut = RampCore(data=get_mem(filename, ICACHE_SIZE))

    dut = config_model_with_cmdline_opts(dut, cmdline_opts, duts=[])
    dut.apply(DefaultPassGroup(linetrace=LNTRC, vcdwave="vcd/test_ramp_core_bge_verilog"))
    dut.sim_reset()

    fibo_a = 0
    fibo_b = 1
    c = 0x11000000
    for x in range(100):
        dut.sim_tick()
        if dut.io_bus_out.en & (dut.io_bus_out.msg.addr != c):
            c = c + 4
            assert dut.io_bus_out.msg.data == fibo_a + fibo_b
            fibo_a, fibo_b = fibo_b, fibo_a + fibo_b
    # Checking that output was asserted multiple times
    assert c > 0x11000010

def test_jal_verilog(cmdline_opts):
    # test always take unconditional jump without worrying about register renaming
    # Using MMIO

    filename = "tests/input_files/test_jal_verilog.bin"
    dut = RampCore(data=get_mem(filename, ICACHE_SIZE))

    dut = config_model_with_cmdline_opts(dut, cmdline_opts, duts=[])
    dut.apply(DefaultPassGroup(linetrace=LNTRC, vcdwave="vcd/test_ramp_core_jal_verilog"))
    dut.sim_reset()

    fibo_a = 0
    fibo_b = 1
    c = 0x11000000
    for x in range(100):
        dut.sim_tick()
        if dut.io_bus_out.en & (dut.io_bus_out.msg.addr != c):
            c = c + 4
            assert dut.io_bus_out.msg.data == fibo_a + fibo_b
            fibo_a, fibo_b = fibo_b, fibo_a + fibo_b
    # Checking that output was asserted multiple times
    assert c > 0x11000010


def test_beq_verilog(cmdline_opts):
    # test beq, using MMIO NOT working rn
    filename = "tests/input_files/test_beq_verilog.bin"
    dut = RampCore(data=get_mem(filename, ICACHE_SIZE))

    dut = config_model_with_cmdline_opts(dut, cmdline_opts, duts=[])

    dut.apply(DefaultPassGroup(linetrace=LNTRC, vcdwave="vcd/test_ramp_core_beq_verilog"))
    dut.sim_reset()

    # running program
    for x in range(30):
        dut.sim_tick()
        if dut.io_bus_out.en:
            break

    assert dut.io_bus_out.msg == 25
    assert dut.io_bus_out.addr == 0x11000000
    dut.sim_tick()
    assert dut.io_bus_out.msg == 30
    assert dut.io_bus_out.addr == 0x11000004




