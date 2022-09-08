from pymtl3 import Component, InPort, clog2, update, OutPort
from pymtl3.stdlib.ifcs import RecvIfcRTL, SendIfcRTL

from src.cl.reorder_buffer import ROBEntry, ROBEntryUop
from src.cl.memory_unit import LoadStoreEntry

from src.common.consts import (
    MEM_STORE,
    MEM_SW,
    S_TYPE,
    NUM_PHYS_REGS,
    B_TYPE,
    J_TYPE,
)
from src.common.interfaces import BranchUpdate


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
        # for branch prediction
        s.br_update = SendIfcRTL(BranchUpdate)

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

        @update
        def br_updt():
            # handling single branch prediction output, with multiple uops
            # first uop that is a branch is the one that is committed
            s.br_update.en @= 0
            s.br_update.msg @= BranchUpdate(0, 0, 0)
            for x in range(width):
                s.commit_units[x].br_update.rdy @= 0
                if s.commit_units[x].br_update.en & ~s.br_update.en:
                    s.br_update.en @= 1
                    s.br_update.msg @= s.commit_units[x].br_update.msg
                    s.commit_units[x].br_update.rdy @= s.br_update.rdy

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
        # for branch prediction
        s.br_update = SendIfcRTL(BranchUpdate)

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

            s.br_update.en @= 0
            s.br_update.msg.target @= 0
            s.br_update.msg.mispredict @= 0
            s.br_update.msg.tag @= 0

            # writeback loads / arithmetic to registers
            if s.in_.valid:
                # handling branchs TODO: need to handle JALR and linking registers (i-type)
                if (s.in_.optype == B_TYPE) | (s.in_.optype == J_TYPE):
                    s.br_update.en @= 1
                    s.br_update.msg.target @= s.in_.br_target
                    s.br_update.msg.mispredict @= s.in_.br_mispredict
                    s.br_update.msg.tag @= s.in_.br_tag
                # writeback stores to memory
                elif s.in_.optype == S_TYPE:
                    s.store_out.en @= 1
                    s.store_out.msg.addr @= s.in_.store_addr
                    s.store_out.msg.data @= s.in_.data
                    s.store_out.msg.mem_q_idx @= s.in_.mem_q_idx
                    s.stale_out @= 0
                    s.ready_out @= 0
                # writeback to registers
                else:
                    s.reg_wb_en @= 1
                    s.reg_wb_addr @= s.in_.prd
                    s.reg_wb_data @= s.in_.data
                    s.stale_out @= s.in_.stale
                    s.ready_out @= s.in_.prd

