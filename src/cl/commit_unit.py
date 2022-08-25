from pymtl3 import Component, InPort, clog2, update, OutPort
from src.cl.reorder_buffer import ROBEntry, ROBEntryUop
from src.cl.decode import MEM_STORE, MEM_SW, S_TYPE, DualMicroOp, NUM_PHYS_REGS
from src.cl.memory_unit import LoadStoreEntry
from pymtl3.stdlib.ifcs import RecvIfcRTL, SendIfcRTL


class CommitUnit(Component):
    def construct(s, width=2):
        # committed entries from ROB
        s.in_ = InPort(ROBEntry)
        s.reg_wb_addr = [OutPort(clog2(NUM_PHYS_REGS)) for _ in range(width)]
        s.reg_wb_data = [OutPort(32) for _ in range(width)]
        s.reg_wb_en = [OutPort(1) for _ in range(width)]

        s.store_out = [SendIfcRTL(LoadStoreEntry) for _ in range(width)]
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

            s.commit_units[x].store_out //= s.store_out[x]

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
        s.store_out = SendIfcRTL(LoadStoreEntry)

        # for updating freelist
        s.stale_out = OutPort(clog2(NUM_PHYS_REGS))
        # for updating busy table
        s.ready_out = OutPort(clog2(NUM_PHYS_REGS))

        @update
        def comb_():
            s.reg_wb_en @= 0
            s.reg_wb_addr @= 0
            s.reg_wb_data @= 0
            s.stale_out @= 0
            s.ready_out @= 0

            s.store_out.en @= 0
            s.store_out.msg.addr @= 0
            s.store_out.msg.data @= 0
            s.store_out.msg.rob_idx @= 0
            s.store_out.msg.mem_q_idx @= 0
            s.store_out.msg.op @= MEM_STORE

            # writeback loads / arithmetic to registers
            if ~(s.in_.optype == S_TYPE) & s.in_.valid:
                s.reg_wb_en @= 1
                s.reg_wb_addr @= s.in_.prd
                s.reg_wb_data @= s.in_.data
                s.stale_out @= s.in_.stale
                s.ready_out @= s.in_.prd

            # writeback stores to memory
            elif s.in_.valid:
                s.store_out.en @= 1
                s.store_out.msg.addr @= s.in_.store_addr
                s.store_out.msg.data @= s.in_.data
                s.store_out.msg.mem_q_idx @= s.in_.mem_q_idx
                s.stale_out @= 0
                s.ready_out @= 0
