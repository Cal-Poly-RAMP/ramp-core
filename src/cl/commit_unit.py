from pymtl3 import Component, InPort, clog2, update, OutPort
from src.cl.reorder_buffer import ROBEntry, ROBEntryUop
from src.cl.decode import S_TYPE, DualMicroOp, NUM_PHYS_REGS

class CommitUnit(Component):
    def construct(s, width=2):
        # committed entries from ROB
        s.in_ = InPort(ROBEntry)
        s.reg_wb_addr = [OutPort(clog2(NUM_PHYS_REGS)) for _ in range(width)]
        s.reg_wb_data = [OutPort(32) for _ in range(width)]
        s.reg_wb_en = [OutPort(1) for _ in range(width)]
        # for updating freelist
        s.stale_out = [OutPort(clog2(NUM_PHYS_REGS)) for _ in range(width)]
        # for updating busy table
        s.ready_out = [OutPort(clog2(NUM_PHYS_REGS)) for _ in range(width)]

        s.commit_units = [SingleCommit() for _ in range(width)]
        s.commit_units[0].in_ //= s.in_.uop1_entry
        s.commit_units[1].in_ //= s.in_.uop2_entry
        for x in range(width):
            s.commit_units[x].reg_wb_addr //= s.reg_wb_addr[x]
            s.commit_units[x].reg_wb_data //= s.reg_wb_data[x]
            s.commit_units[x].reg_wb_en //= s.reg_wb_en[x]
            s.commit_units[x].stale_out //= s.stale_out[x]
            s.commit_units[x].ready_out //= s.ready_out[x]

# For each uop in rob entry
class SingleCommit(Component):
    def construct(s):
        s.in_ = InPort(ROBEntryUop)
        # writeback to registers
        s.reg_wb_addr = OutPort(clog2(NUM_PHYS_REGS))
        s.reg_wb_data = OutPort(32)
        s.reg_wb_en = OutPort(1)
        # writeback to memory
        s.mem_wb_addr = OutPort(32)
        s.mem_wb_data = OutPort(32)
        s.mem_wb_en = OutPort(1)

        # for updating freelist
        s.stale_out = OutPort(clog2(NUM_PHYS_REGS))
        # for updating busy table
        s.ready_out = OutPort(clog2(NUM_PHYS_REGS))

        @update
        def comb_():
            # writeback stores to memory
            if s.in_.optype == S_TYPE:
                s.mem_wb_en @= 0
                s.mem_wb_addr @= 0
                s.mem_wb_data @= 0
                s.stale_out @= 0
                s.ready_out @= 0
            # writeback loads / arithmetic to registers
            else:
                s.reg_wb_en @= 1
                s.reg_wb_addr @= s.in_.prd
                s.reg_wb_data @= s.in_.data
                s.stale_out @= s.in_.stale
                s.ready_out @= s.in_.prd


