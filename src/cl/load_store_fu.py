from pymtl3 import Component, InPort, OutPort, update, sext, clog2, Bits, zext
from pymtl3.stdlib.ifcs import RecvIfcRTL, SendIfcRTL

from src.common.consts import (
    MEM_FLAG,
    NUM_PHYS_REGS,
    MEM_LOAD,
    MEM_STORE,
    MEM_SB,
    MEM_SH,
    MEM_SW,
    ROB_SIZE,
    MEM_Q_SIZE,
)
from src.cl.memory_unit import LoadStoreEntry

# Calculates address of a load
# Calculates address, and gets data for a store
class LoadStoreFU(Component):
    def construct(s):
        s.rs1_din = InPort(32)
        s.rs2_din = InPort(32)
        s.prd_addr_in = InPort(clog2(NUM_PHYS_REGS))
        s.imm_in = InPort(32)
        s.rob_idx_in = InPort(clog2(ROB_SIZE))
        s.mem_q_idx_in = InPort(clog2(MEM_Q_SIZE))
        s.enable = InPort()

        # load 0, store 1
        s.funct = InPort(4)
        # to memory unit
        s.load_out = SendIfcRTL(LoadStoreEntry)
        # to reorder buffer
        s.store_out = SendIfcRTL(LoadStoreEntry)

        @update
        def updt():
            s.load_out.en @= s.enable & ((s.funct & MEM_FLAG) == MEM_LOAD)
            s.load_out.msg.op @= s.funct
            s.load_out.msg.addr @= sext(s.imm_in, 32) + s.rs1_din
            s.load_out.msg.data @= 0
            s.load_out.msg.rob_idx @= s.rob_idx_in
            s.load_out.msg.mem_q_idx @= s.mem_q_idx_in

            s.store_out.en @= s.enable & ((s.funct & MEM_FLAG) == MEM_STORE)
            s.store_out.msg.op @= s.funct
            s.store_out.msg.addr @= sext(s.imm_in, 32) + s.rs1_din
            s.store_out.msg.rob_idx @= s.rob_idx_in
            s.store_out.msg.mem_q_idx @= s.mem_q_idx_in

            # Getting data for store
            # TODO: update for 64 bit
            # calculating slice for subword
            if s.funct == MEM_SB:
                s.store_out.msg.data @= zext(s.rs2_din[0:8], 32)
            elif s.funct == MEM_SH:
                s.store_out.msg.data @= zext(s.rs2_din[0:16], 32)
            elif s.funct == MEM_SW:
                s.store_out.msg.data @= s.rs2_din
            else:
                s.store_out.msg.data @= s.rs2_din
            # TODO: CL debugging
            # assert ~s.enable | s.load_out.en | s.store_out.en, "Invalid funct"

    def line_trace(s):
        return (
            f"load out: {s.load_out.msg if s.load_out.en else '-'} "
            f"store out: {s.store_out.msg if s.store_out.en else '-'}"
        )
