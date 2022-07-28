from pymtl3 import *
from pymtl3 import Bits5, Bits6
from pymtl3.stdlib.basic_rtl.encoders import Encoder
from src.fl.util import cascading_priority_encoder

# from src.cl.fetch_stage import FetchPacket
# from src.cl.decoder import DualMicroOp
NUM_ISA_REGS = 32
ISA_REG_BITWIDTH = 5

NUM_PHYS_REGS = 64
PHYS_REG_BITWIDTH = 6

REG_RENAME_ERR = "Tried to rename a register when no physical registers are free. Halting not implemented yet. 🤬"


@bitstruct
class LogicalRegs:
    lrd: Bits5  # logical destination register
    lrs1: Bits5  # logical source register 1
    lrs2: Bits5  # logical source register 2


@bitstruct
class PhysicalRegs:
    prd: Bits6  # physical dest register TODO: get bitwidth from phys reg file size
    prs1: Bits6  # physical source register 1
    prs2: Bits6  # physical source register 2
    stale: Bits6  # stale physical register


class RegisterRename(Component):
    def construct(s):
        # interface
        s.inst1_lregs = InPort(LogicalRegs)
        s.inst2_lregs = InPort(LogicalRegs)
        s.inst2_pregs = OutPort(PhysicalRegs)
        s.inst1_pregs = OutPort(PhysicalRegs)

        s.free_list = OutPort(NUM_PHYS_REGS)
        s.busy_table = OutPort(NUM_PHYS_REGS)

        # map tables
        s.map_table = [0] * NUM_ISA_REGS

        # internal freelist
        s._free_list = Bits(NUM_PHYS_REGS, 0)  # implemented as bit vector 1 -> free
        s.free_list //= s._free_list

        # internal busy table
        s._busy_table = Bits(NUM_PHYS_REGS, 0)
        s.busy_table //= s._busy_table

        s.pdst1 = 0
        s.pdst2 = 0

        @update
        def rename_comb():
            # rename inst1
            s.inst1_pregs.prs1 @= s.map_table[s.inst1_lregs.lrs1]
            s.inst1_pregs.prs2 @= s.map_table[s.inst1_lregs.lrs2]

            # rename inst2
            s.inst2_pregs.prs1 @= s.map_table[s.inst2_lregs.lrs1]
            s.inst2_pregs.prs2 @= s.map_table[s.inst2_lregs.lrs2]

        @update_once
        def rename_once():
            # resetting
            if(s.reset == 1):
                s._free_list @= -1 << 1 # for zero register
                s._busy_table @= 0
                return

            # getting next two free registers
            s.pdst1, s.pdst2 = cascading_priority_encoder(2, s._free_list)

            # exceptions
            if (s.inst1_lregs.lrd != 0 ^ s.inst2_lregs.lrd != 0) and s._free_list == 0:
                raise Exception(REG_RENAME_ERR)
            if (s.inst1_lregs.lrd != 0 and s.inst2_lregs.lrd != 0) and s._free_list & ~(
                Bits(NUM_PHYS_REGS, 1) << s.pdst1
            ) == 0:
                raise Exception(REG_RENAME_ERR)

            if s.inst1_lregs.lrd != 0:
                s.inst1_pregs.prd @= s.pdst1
                s._free_list = s._free_list & ~(Bits(NUM_PHYS_REGS, 1) << s.pdst1)
                s.map_table[s.inst1_lregs.lrd] = s.pdst1

            if s.inst2_lregs.lrd != 0:
                s.inst2_pregs.prd @= s.pdst2
                s._free_list @= s._free_list & ~(Bits(NUM_PHYS_REGS, 1) << s.pdst2)
                s.map_table[s.inst2_lregs.lrd] = s.pdst2

            print(s.line_trace())

    def line_trace(s):
        return "REG RENAME: " "inst1_lregs: {} inst2_lregs: {} ".format(
            s.inst1_lregs, s.inst2_lregs
        ) + "inst1_pregs: {} inst2_pregs: {} ".format(
            s.inst1_pregs, s.inst2_pregs
        ) + "free_list: 0x{} busy_table: 0x{} ".format(
            s._free_list, s._busy_table
        ) + "map_table: {}".format(s.map_table)
