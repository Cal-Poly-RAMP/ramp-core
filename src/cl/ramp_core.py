from pymtl3 import Component, update, mk_bits

from src.cl.decode import (
    ALU_FUNCT_UNIT,
    MEM_FUNCT_UNIT,
    WINDOW_SIZE,
    MEM_Q_SIZE,
    MEM_SIZE,
    NO_OP,
    R_TYPE,
    DualMicroOp,
    NUM_PHYS_REGS,
    Wire,
    OutPort,
    Bits,
)
from src.cl.commit_unit import CommitUnit
from src.cl.fetch_stage import FetchPacket, FetchStage
from src.cl.decode import Decode
from src.cl.dispatch import Dispatch
from src.cl.reorder_buffer import ReorderBuffer, ExecToROB
from src.cl.issue_queue import IssueQueue
from src.cl.alu import ALU
from src.cl.memory_unit import MemoryUnit
from src.cl.load_store_fu import LoadStoreFU

from pymtl3.stdlib.basic_rtl.registers import RegEnRst
from pymtl3.stdlib.basic_rtl.register_files import RegisterFile


class RampCore(Component):
    def construct(s, memory_size=MEM_SIZE, data=None):
        # FRONT END
        # (1) Fetch stage
        s.fetch_stage = FetchStage()

        # pipeline register 1 - between fetch and decode
        s.pr1 = RegEnRst(FetchPacket, reset_value=FetchPacket(0, 0, 0, 0))
        s.pr1.in_ //= s.fetch_stage.fetch_packet

        # (2) Decode stage
        s.decode = Decode()
        s.decode.fetch_packet //= s.pr1.out

        s.dual_uop = OutPort(DualMicroOp)
        s.dual_uop //= s.decode.dual_uop

        s.busy_table = OutPort(NUM_PHYS_REGS)
        s.busy_table //= s.decode.busy_table

        # pipline register - between decode and dispatch
        s.pr2 = RegEnRst(DualMicroOp, reset_value=DualMicroOp(NO_OP, NO_OP))
        s.pr2.in_ //= s.decode.dual_uop

        # BACK END - executes the micro ops
        # (3) dispatch stage - sends microops to ROB, and correct execution path
        s.dispatch = Dispatch()
        s.dispatch.in_ //= s.pr2.out

        # reorder buffer - stores microops so they can be committed in order
        s.reorder_buffer = ReorderBuffer()
        s.reorder_buffer.write_in //= s.dispatch.to_rob
        s.reorder_buffer.rob_tail //= s.dispatch.rob_idx

        # (4) issue stage - store microops until they are ready to be issued
        s.int_issue_queue = IssueQueue()
        s.int_issue_queue.duop_in //= s.dispatch.to_int_issue
        s.int_issue_queue.busy_table //= s.decode.busy_table

        s.mem_issue_queue = IssueQueue()
        s.mem_issue_queue.duop_in //= s.dispatch.to_mem_issue
        s.mem_issue_queue.busy_table //= s.decode.busy_table

        # register file - physical registers
        s.register_file = RegisterFile(
            mk_bits(32), nregs=NUM_PHYS_REGS, rd_ports=4, wr_ports=2, const_zero=True
        )
        s.register_file.raddr[0] //= s.int_issue_queue.uop_out.prs1
        s.register_file.raddr[1] //= s.int_issue_queue.uop_out.prs2
        s.register_file.raddr[2] //= s.mem_issue_queue.uop_out.prs1
        s.register_file.raddr[3] //= s.mem_issue_queue.uop_out.prs2

        # (5) execution stage - execute the microops
        # ALU
        s.alu = ALU(mk_bits(32))
        s.alu.a //= s.register_file.rdata[0]
        s.alu.op //= s.int_issue_queue.uop_out.funct_op

        # load/store execution unit
        s.load_store_unit = LoadStoreFU()
        s.load_store_unit.rs1_din //= s.register_file.rdata[2]
        s.load_store_unit.rs2_din //= s.register_file.rdata[3]
        s.load_store_unit.prd_addr_in //= s.mem_issue_queue.uop_out.prd
        s.load_store_unit.imm_in //= s.mem_issue_queue.uop_out.imm
        s.load_store_unit.rob_idx_in //= s.mem_issue_queue.uop_out.rob_idx
        s.load_store_unit.mem_q_idx_in //= s.mem_issue_queue.uop_out.mem_q_idx
        s.load_store_unit.funct //= s.mem_issue_queue.uop_out.funct_op

        # (6) commit unit - commit the changes
        s.commit_unit = CommitUnit()
        s.commit_unit.in_ //= s.reorder_buffer.commit_out
        for i in range(2):
            s.commit_unit.reg_wb_addr[i] //= s.register_file.waddr[i]
            s.commit_unit.reg_wb_data[i] //= s.register_file.wdata[i]
            s.commit_unit.reg_wb_en[i] //= s.register_file.wen[i]
            s.commit_unit.stale_out[i] //= s.decode.stale_in[i]
            s.commit_unit.ready_out[i] //= s.decode.ready_in[i]

        # Memory
        s.memory_unit = MemoryUnit(
            queue_size=MEM_Q_SIZE, memory_size=memory_size, window_size=3, data=data
        )
        # allocate space in memory queue in decode unit
        s.memory_unit.allocate_in.msg //= s.decode.mem_q_allocate
        s.memory_unit.allocate_in.en //= Bits(1, 1)
        # update buffer locations with load data from execute unit
        s.memory_unit.update_in[0] //= s.load_store_unit.load_out
        # update buffer locations with store data from commit unit
        s.memory_unit.update_in[1] //= s.commit_unit.store_out[0]
        s.memory_unit.update_in[2] //= s.commit_unit.store_out[1]
        # for updating mem_q_idx in decode unit
        s.dispatch.mem_q_tail //= s.memory_unit.mem_q_tail

        # (6) writeback
        # INT writeback
        s.reorder_buffer.op_complete.int_rob_idx //= s.int_issue_queue.uop_out.rob_idx
        s.reorder_buffer.op_complete.int_data //= s.alu.out
        # STORE writeback
        s.reorder_buffer.op_complete.store_rob_idx //= (
            s.load_store_unit.store_out.msg.rob_idx
        )
        s.reorder_buffer.op_complete.store_data //= s.load_store_unit.store_out.msg.data
        s.reorder_buffer.op_complete.store_addr //= s.load_store_unit.store_out.msg.addr
        s.reorder_buffer.op_complete.store_rob_complete //= (
            s.load_store_unit.store_out.en
        )
        s.reorder_buffer.op_complete.store_mem_q_idx //= s.load_store_unit.store_out.msg.mem_q_idx
        # LOAD writeback
        s.reorder_buffer.op_complete.load_rob_idx //= s.memory_unit.load_out.msg.rob_idx
        s.reorder_buffer.op_complete.load_data //= s.memory_unit.load_out.msg.data
        s.reorder_buffer.op_complete.load_rob_complete //= s.memory_unit.load_out.en

        @update
        def update_cntrl():
            s.pr1.en @= ~s.reset
            s.pr2.en @= ~s.reset

            s.reorder_buffer.op_complete.int_rob_complete @= (
                s.int_issue_queue.uop_out.funct_unit == ALU_FUNCT_UNIT
            )
            s.load_store_unit.enable @= (
                s.mem_issue_queue.uop_out.funct_unit == MEM_FUNCT_UNIT
            )
            # Immediate logic
            if s.int_issue_queue.uop_out.optype != R_TYPE:
                s.alu.b @= s.int_issue_queue.uop_out.imm
            else:
                s.alu.b @= s.register_file.rdata[1]

    def line_trace(s):
        return (
            f"\npr1: {s.pr1.line_trace()}\n\n"
            f"pr2: {s.pr2.line_trace()}\n\n"
            # f"pr3: {s.pr3.line_trace()}\n\n"
            f"register_file:\t{[r.uint() for r in s.register_file.regs]}\n\n"
            f"busy_table:\t{[b.uint() for b in s.busy_table]}\n\n"
            f"map_table: {[b.uint() for b in s.decode.register_rename.map_table]}\n\n"
            f"free_list: {bin(s.decode.register_rename.free_list)}\n\n"
            f"int_issue_queue: {s.int_issue_queue.line_trace()}\n"
            f"alu: {s.alu.line_trace()}\n\n"
            f"mem_issue_queue: {s.mem_issue_queue.line_trace()}\n"
            f"load_store_fu: {s.load_store_unit.line_trace()}\n\n"
            f"commit out uop1: 0x{s.reorder_buffer.commit_out.uop1_entry.data}\n\n"
            f"commit out uop2: 0x{s.reorder_buffer.commit_out.uop2_entry.data}\n\n"
            f"memory unit: \n{s.memory_unit.line_trace()}\n\n"
            f"reorder buffer: {s.reorder_buffer.line_trace()}\n\n"
        )
