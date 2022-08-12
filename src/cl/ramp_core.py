from distutils.command.install import INSTALL_SCHEMES
from pymtl3 import Component, update, mk_bits

from src.cl.decode import (
    ALU_FUNCT_UNIT,
    INT_ISSUE_UNIT,
    MEM_FUNCT_UNIT,
    NO_OP,
    DualMicroOp,
    MicroOp,
    NUM_PHYS_REGS,
    Wire,
    OutPort,
)
from src.cl.front_end import FrontEnd
from src.cl.fetch_stage import INSTR_WIDTH, PC_WIDTH, FetchPacket, FetchStage
from src.cl.decode import Decode
from src.cl.dispatch import Dispatch
from src.cl.reorder_buffer import ReorderBuffer, ExecToROB
from src.cl.issue_queue import IssueQueue
from src.cl.alu import ALU

from pymtl3.stdlib.basic_rtl.registers import RegEnRst
from pymtl3.stdlib.basic_rtl.register_files import RegisterFile


class RampCore(Component):
    def construct(s):
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
        # (3) dispatch - sends microops to ROB, and correct execution path
        s.dispatch = Dispatch()
        s.dispatch.in_ //= s.pr2.out

        # reorder buffer - stores microops so they can be committed in order
        s.reorder_buffer = ReorderBuffer()
        s.reorder_buffer.write_in //= s.dispatch.to_rob
        s.reorder_buffer.rob_tail //= s.dispatch.rob_idx

        # (4) issue queues - store microops until they are ready to be issued
        s.int_issue_queue = IssueQueue()
        s.int_issue_queue.duop_in //= s.dispatch.to_int_issue
        s.int_issue_queue.busy_table //= s.decode.busy_table

        # pipeline regiater - between issue queues and register files
        s.pr3 = RegEnRst(MicroOp, reset_value=NO_OP)
        s.pr3.in_ //= s.int_issue_queue.uop_out

        # register file - physical registers
        s.register_file = RegisterFile(
            mk_bits(32), nregs=NUM_PHYS_REGS, rd_ports=2, wr_ports=1, const_zero=True
        )
        s.register_file.raddr[0] //= s.pr3.out.prs1
        s.register_file.raddr[1] //= s.pr3.out.prs2

        # (5) execution units - execute the microops TODO:handle immediates
        # ALU
        s.alu = ALU(mk_bits(32))
        s.alu.a //= s.register_file.rdata[0]
        s.alu.b //= s.register_file.rdata[1]
        s.alu.op //= s.pr3.out.funct_op

        s.reorder_buffer.op_complete.int_rob_idx //= s.pr3.out.rob_idx
        s.reorder_buffer.op_complete.int_data //= s.alu.out

        # commit unit - commit the changes
        # ...

        @update
        def update_cntrl():
            s.pr1.en @= ~s.reset
            s.pr2.en @= ~s.reset
            s.pr3.en @= ~s.reset

            s.reorder_buffer.op_complete.int_rob_complete @= (
                s.pr3.out.funct_unit == ALU_FUNCT_UNIT
            )
            s.reorder_buffer.op_complete.mem_rob_complete @= (
                s.pr3.out.funct_unit == MEM_FUNCT_UNIT
            )

    def line_trace(s):
        return (
            f"\npr1: {s.pr1.line_trace()}\n\n"
            f"pr2: {s.pr2.line_trace()}\n\n"
            f"pr3: {s.pr3.line_trace()}\n\n"
            f"register_file: {[r.uint() for r in s.register_file.regs]}\n\n"
            f"busy_table: {[b.uint() for b in s.busy_table]}\n\n"
            f"map_table: {[b.uint() for b in s.decode.register_rename.map_table]}\n\n"
            f"int_issue_queue: {s.int_issue_queue.line_trace()}\n\n"
            f"commit out uop1: 0x{s.reorder_buffer.commit_out.uop1_entry.data}\n\n"
            f"commit out uop2: 0x{s.reorder_buffer.commit_out.uop2_entry.data}\n\n"
        )
