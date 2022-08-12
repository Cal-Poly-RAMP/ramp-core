from pymtl3 import *
from src.fl.util import csv_to_vector
from src.cl.ramp_core import RampCore
from src.cl.fetch_stage import FetchPacket
from pymtl3.stdlib.test_utils import config_model_with_cmdline_opts
from src.cl.decode import (
    DualMicroOp,
    MicroOp,
    RTYPE_OPCODE,
    ITYPE_OPCODE1,
    ITYPE_OPCODE2,
    ITYPE_OPCODE3,
    STYPE_OPCODE,
    BTYPE_OPCODE,
    UTYPE_OPCODE1,
    UTYPE_OPCODE2,
    JTYPE_OPCODE,
    CSRTYPE_OPCODE,

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

# def test_vector( cmdline_opts ):
#     # Configure the model from command line flags
#     model = RampCoreTestHarness(RampCore())
#     model.elaborate()

#     # Loading program
#     print("Loading program...")
#     model.ramp_core.front_end.fetch_stage.icache.load_file('tests/input_files/test_ramp_core1.bin')
#     print("Program loaded.")
#     print(model.ramp_core.front_end.fetch_stage.icache.memory.mem)
#     # Run a test vector
#     test_vector = csv_to_vector( "tests/input_files/test_ramp_core_vector.csv" )
# run_test_vector_sim( model,test_vector, cmdline_opts)


def test_system(cmdline_opts):
    # Configure the model from command line flags
    dut = RampCore()
    dut = config_model_with_cmdline_opts(dut, cmdline_opts, duts=[])
    dut.apply(DefaultPassGroup(linetrace=True))
    dut.sim_reset()
    dut.fetch_stage.icache.load_file("tests/input_files/test_ramp_core1.bin")

    # 1 FETCH
    dut.sim_tick()
    # inst1: add x3, x2, x1 inst2: sub x13, x12, x11
    fp = FetchPacket(inst1=0xB3011100, inst2=0xB306B640, pc=0, valid=1)

    # Fetch | Decode
    assert dut.pr1.out == fp
    # Decode | Dispatch/Issue
    assert not dut.pr2.out
    # Dispatch/Issue | Execute
    assert not dut.pr3.out

    # 2 DECODE
    # dut.sim_tick()
    # nfp = FetchPacket(inst1=0, inst2=0, pc=0, valid=1)
    # duop = DualMicroOp(
    #     uop1=MicroOp(
    #         optype=
    #     )
    # )
    # # Fetch | Decode
    # assert dut.pr1.out == nfp
    # # Decode | Dispatch/Issue
    # assert not dut.pr2.out
    # # Dispatch/Issue | Execute
    # assert not dut.pr3.out

    # # Cleanup
    # dut.sim_tick()
    # dut.sim_tick()
