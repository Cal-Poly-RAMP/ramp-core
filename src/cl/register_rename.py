from pymtl3 import (
    Bits,
    Component,
    InPort,
    OutPort,
    Wire,
    bitstruct,
    mk_bits,
    update,
    update_ff,
    zext,
    clog2,
)
from pymtl3.stdlib.ifcs import RecvIfcRTL, SendIfcRTL

from src.common.interfaces import (
    LogicalRegs,
    PhysicalRegs,
    PRegBusy,
    BranchUpdate
)
from src.common.consts import (
    NUM_ISA_REGS,
    NUM_PHYS_REGS,
)

REG_RENAME_ERR = "Tried to rename a register when no physical registers are free. Halting not implemented yet."


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

        # register to be freed (from commit stage)
        s.stale_in = [InPort(clog2(NUM_PHYS_REGS)) for _ in range(2)]
        # register to be marked as 'not busy' (from commit stage)
        s.ready_in = [InPort(clog2(NUM_PHYS_REGS)) for _ in range(2)]

        # map tables
        s.map_table = [Wire(clog2(NUM_PHYS_REGS)) for _ in range(NUM_ISA_REGS)]

        s.map_table_wr1 = Wire(clog2(NUM_PHYS_REGS))
        s.map_table_wr2 = Wire(clog2(NUM_PHYS_REGS))

        # internal freelist implemented as bit vector 1 -> free
        s.free_list_next = Wire(NUM_PHYS_REGS)  # -1 << 1
        s.free_list_reset = Bits(NUM_PHYS_REGS, -1 << 1)

        # internal busy table
        s.busy_table_next = Wire(NUM_PHYS_REGS)

        s.pdst1 = Wire(clog2(NUM_PHYS_REGS))
        s.pdst2 = Wire(clog2(NUM_PHYS_REGS))

        s.ONE = Bits(NUM_PHYS_REGS, 1)

        # for deallocating and recalling state for predicted branches TODOL\
        s.br_update = RecvIfcRTL(BranchUpdate)
        s.br_update.rdy //= Bits(1,1)

        @update
        def rename_comb():
            # Combinatorially getting physical source registers from map table
            # and getting physical dest registers from free list
            # TODO: add assert statements for when physical registers are full

            # *combinatorially* getting dest registers, but not updating tables
            # pdst1, pdst2 = cascading_priority_encoder(2, s.free_list_next)
            s.pdst1 @= 0
            s.pdst2 @= 0
            for i in range(NUM_PHYS_REGS):
                if s.free_list[i]:
                    if s.pdst1 == 0:
                        s.pdst1 @= i
                    elif s.pdst2 == 0:
                        s.pdst2 @= i
            # making sure that there are free registers
            # assert s.pdst1 != 0 or s.pdst2 != 0

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
            s.inst1_pregs_busy.prs1 @= s.busy_table[s.inst1_pregs.prs1]
            s.inst1_pregs_busy.prs2 @= s.busy_table[s.inst1_pregs.prs2]

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
                s.inst2_pregs_busy.prs1 @= s.busy_table[s.inst2_pregs.prs2]

            if (s.inst2_lregs.lrs2 == s.inst1_lregs.lrd) & (s.inst1_lregs.lrd != 0):
                # inst2 dependent on inst1. inst2 prs2 = pdst1 and is busy
                s.inst2_pregs.prs2 @= s.pdst1
                s.inst2_pregs_busy.prs2 @= 1
            else:
                s.inst2_pregs.prs2 @= s.map_table[s.inst2_lregs.lrs2]
                s.inst2_pregs_busy.prs2 @= s.busy_table[s.inst2_pregs.prs2]

            # nextstate for updating free_list, map_table, busy_table
            if s.reset:
                s.free_list_next @= s.free_list_reset
                s.busy_table_next @= 0
            else:
                # updating tables with newely allocated registers
                if (s.inst1_lregs.lrd != 0) ^ (s.inst2_lregs.lrd != 0):
                    s.free_list_next @= s.free_list_next & ~(
                        s.ONE << zext(s.pdst1, NUM_PHYS_REGS)
                    )
                    s.busy_table_next @= s.busy_table | (
                        s.ONE << zext(s.pdst1, NUM_PHYS_REGS)
                    )
                    if s.inst1_lregs.lrd:
                        s.map_table_wr1 @= s.pdst1
                        s.map_table_wr2 @= 0
                    elif s.inst2_lregs.lrd:
                        s.map_table_wr1 @= 0
                        s.map_table_wr2 @= s.pdst1

                elif (s.inst1_lregs.lrd != 0) & (s.inst2_lregs.lrd != 0):
                    # ensuring there are registers to allocate
                    s.free_list_next @= (
                        s.free_list_next
                        & ~(s.ONE << zext(s.pdst1, NUM_PHYS_REGS))
                        & ~(s.ONE << zext(s.pdst2, NUM_PHYS_REGS))
                    )
                    s.busy_table_next @= (
                        s.busy_table
                        | s.ONE << zext(s.pdst1, NUM_PHYS_REGS)
                        | s.ONE << zext(s.pdst2, NUM_PHYS_REGS)
                    )
                    s.map_table_wr1 @= s.pdst1
                    s.map_table_wr2 @= s.pdst2
                else:
                    s.busy_table_next @= s.busy_table
                    s.map_table_wr1 @= s.map_table[s.inst1_lregs.lrd]
                    s.map_table_wr2 @= s.map_table[s.inst2_lregs.lrd]

            # updating free_list, busy_table
            for i in range(2):
                if s.stale_in[i]:
                    s.free_list_next @= s.free_list_next | (
                        s.ONE << zext(s.stale_in[i], NUM_PHYS_REGS)
                    )
                if s.ready_in[i]:
                    s.busy_table_next @= s.busy_table_next & ~(
                        s.ONE << zext(s.ready_in[i], NUM_PHYS_REGS)
                    )

        @update_ff
        def rename_ff():
            s.free_list <<= s.free_list_next
            s.busy_table <<= s.busy_table_next
            s.map_table[s.inst1_lregs.lrd] <<= s.map_table_wr1
            s.map_table[s.inst2_lregs.lrd] <<= s.map_table_wr2
            # TODO: CL debugging
            # assert s.map_table[0] == 0
            # assert ~((s.inst1_lregs.lrd == 0) ^ (s.map_table_wr1 == 0))
            # assert ~((s.inst2_lregs.lrd == 0) ^ (s.map_table_wr2 == 0))

            # # resetting
            if s.reset == 1:
                for x in range(NUM_ISA_REGS):
                    s.map_table[x] <<= 0

            # checking zero always points to zero

    def line_trace(s):
        return (
            "inst1_lregs: {} inst2_lregs: {} ".format(s.inst1_lregs, s.inst2_lregs)
            + "inst1_pregs: {} inst2_pregs: {} ".format(s.inst1_pregs, s.inst2_pregs)
            + "\n\tfree_list: 0x{} free_list_next: 0x{} busy_table: 0x{} busy_table_next: 0x{}\n".format(
                s.free_list, s.free_list_next, s.busy_table, s.busy_table_next
            )
            + "\tmap_table: {}".format([x.uint() for x in s.map_table])
            + "\n\tmap_table_wr1: {} map_table_wr2: {}".format(
                s.map_table_wr1, s.map_table_wr2
            )
        )
