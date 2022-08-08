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
    lrd: mk_bits(ISA_REG_BITWIDTH)  # logical destination register
    lrs1: mk_bits(ISA_REG_BITWIDTH)  # logical source register 1
    lrs2: mk_bits(ISA_REG_BITWIDTH)  # logical source register 2


@bitstruct
class PhysicalRegs:
    prd: mk_bits(
        PHYS_REG_BITWIDTH
    )  # physical dest register TODO: get bitwidth from phys reg file size
    prs1: mk_bits(PHYS_REG_BITWIDTH)  # physical source register 1
    prs2: mk_bits(PHYS_REG_BITWIDTH)  # physical source register 2
    stale: mk_bits(PHYS_REG_BITWIDTH)  # stale physical register


@bitstruct
class PRegBusy:
    prs1: Bits1
    prs2: Bits1


class RegisterRename(Component):
    def construct(s):
        # interface
        s.inst1_lregs = InPort(LogicalRegs)
        s.inst1_pregs = OutPort(PhysicalRegs)
        s.inst1_pregs_busy = OutPort(PRegBusy)
        s.inst2_lregs = InPort(LogicalRegs)
        s.inst2_pregs = OutPort(PhysicalRegs)
        s.inst2_pregs_busy = OutPort(PRegBusy)

        s.free_list = OutPort(NUM_PHYS_REGS)
        s.busy_table = OutPort(NUM_PHYS_REGS)

        # map tables
        s.map_table = [Bits(PHYS_REG_BITWIDTH, 0) for _ in range(NUM_ISA_REGS)]

        # internal freelist implemented as bit vector 1 -> free
        s._free_list = Bits(NUM_PHYS_REGS, -1 << 1)
        s.free_list //= s._free_list

        # internal busy table
        s._busy_table = Bits(NUM_PHYS_REGS, 0)
        s.busy_table //= s._busy_table

        s.pdst1 = Wire(PHYS_REG_BITWIDTH)
        s.pdst2 = Wire(PHYS_REG_BITWIDTH)

        s.ONE = Bits(NUM_PHYS_REGS, 1)

        @update
        def rename_comb():
            # Combinatorially getting physical source registers from map table
            # and getting physical dest registers from free list

            # *combinatorially* getting dest registers, but not updating tables
            # pdst1, pdst2 = cascading_priority_encoder(2, s._free_list)
            s.pdst1 @= 0
            s.pdst2 @= 0
            for i in range(PHYS_REG_BITWIDTH):
                if s.free_list[i]:
                    if s.pdst1 == 0:
                        s.pdst1 @= i
                    elif s.pdst2 == 0:
                        s.pdst2 @= i

            if s.inst1_lregs.lrd:
                s.inst1_pregs.prd @= s.pdst1
                s.inst2_pregs.prd @= s.pdst2 if s.inst2_lregs.lrd else 0
            elif s.inst2_lregs.lrd:
                s.inst1_pregs.prd @= 0
                s.inst2_pregs.prd @= s.pdst1
            else:
                s.inst1_pregs.prd @= 0
                s.inst2_pregs.prd @= 0

            s.inst1_pregs.prs1 @= s.map_table[s.inst1_lregs.lrs1]
            s.inst1_pregs.prs2 @= s.map_table[s.inst1_lregs.lrs2]
            s.inst1_pregs.stale @= s.map_table[s.inst1_lregs.lrd]
            s.inst1_pregs_busy.prs1 @= s._busy_table[s.inst1_pregs.prs1]
            s.inst1_pregs_busy.prs2 @= s._busy_table[s.inst1_pregs.prs2]

            # bypass network.
            # forward dependent sources from inst2 to inst1. handle stale
            if (s.inst2_lregs.lrd == s.inst1_lregs.lrd) & (s.inst1_lregs.lrd != 0):
                # inst2 dependent on inst1.
                s.inst2_pregs.stale @= s.pdst1
            else:
                s.inst2_pregs.stale @= s.map_table[s.inst2_lregs.lrd]

            if (s.inst2_lregs.lrs1 == s.inst1_lregs.lrd) & (s.inst1_lregs.lrd != 0):
                # inst2 dependent on inst1. inst2 prs1 = pdst1 and is busy
                s.inst2_pregs.prs1 @= s.pdst1
                s.inst2_pregs_busy.prs1 @= 1
            else:
                s.inst2_pregs.prs1 @= s.map_table[s.inst2_lregs.lrs1]
                s.inst2_pregs_busy.prs1 @= s._busy_table[s.inst2_pregs.prs2]

            if (s.inst2_lregs.lrs2 == s.inst1_lregs.lrd) & (s.inst1_lregs.lrd != 0):
                # inst2 dependent on inst1. inst2 prs2 = pdst1 and is busy
                s.inst2_pregs.prs2 @= s.pdst1
                s.inst2_pregs_busy.prs2 @= 1
            else:
                s.inst2_pregs.prs2 @= s.map_table[s.inst2_lregs.lrs2]
                s.inst2_pregs_busy.prs2 @= s._busy_table[s.inst2_pregs.prs2]

        @update_ff
        def rename_ff():
            # resetting
            if s.reset == 1:
                s._free_list @= -1 << 1  # for zero register
                s._busy_table @= 0
                for x in range(NUM_ISA_REGS):
                    s.map_table[x] @= 0
            else:
                # getting next two free registers
                # pdst1, pdst2 = cascading_priority_encoder(2, s._free_list)

                # updating tables with newely allocated registers
                if (s.inst1_lregs.lrd != 0) | (s.inst2_lregs.lrd != 0):
                    # raising exception if not enough registers to allocate
                    # TODO: stall
                    # if s._free_list == 0:
                    #     raise Exception(REG_RENAME_ERR)
                    # updating with first pdst off free list
                    s._free_list @= s._free_list & ~(s.ONE << zext(s.pdst1, NUM_PHYS_REGS))
                    s._busy_table @= s._busy_table | (s.ONE << zext(s.pdst1, NUM_PHYS_REGS))

                    # updating map table with new register
                    if s.inst1_lregs.lrd:
                        s.map_table[s.inst1_lregs.lrd] @= s.pdst1
                    elif s.inst2_lregs.lrd:
                        s.map_table[s.inst2_lregs.lrd] @= s.pdst1

                if (s.inst1_lregs.lrd != 0) & (s.inst2_lregs.lrd != 0):
                    # raising exception if not enough registers to allocate
                    # TODO: stall
                    # if s._free_list & ~(Bits(NUM_PHYS_REGS, 1) << zext(s.pdst1, NUM_PHYS_REGS)) == 0:
                    #     raise Exception(REG_RENAME_ERR)
                    # updating with second pdst off free list
                    s._free_list @= s._free_list & ~(s.ONE << zext(s.pdst2, NUM_PHYS_REGS))
                    s._busy_table @= s._busy_table | (s.ONE << zext(s.pdst2, NUM_PHYS_REGS))

                    # updating map table with new register
                    s.map_table[s.inst1_lregs.lrd] @= s.pdst1
                    s.map_table[s.inst2_lregs.lrd] @= s.pdst2

    def line_trace(s):
        return (
            "inst1_lregs: {} inst2_lregs: {} ".format(s.inst1_lregs, s.inst2_lregs)
            + "inst1_pregs: {} inst2_pregs: {} ".format(s.inst1_pregs, s.inst2_pregs)
            + "\n\tfree_list: 0x{} busy_table: 0x{} \n".format(
                s.free_list, s.busy_table
            )
            + "\tmap_table: {}".format(s.map_table)
        )
