from pymtl3 import Component, update, mk_bits

from src.cl.decoder import DualMicroOp, MicroOp, NUM_PHYS_REGS
from src.cl.front_end import FrontEnd
from src.cl.dispatch import Dispatch
from src.cl.reorder_buffer import ReorderBuffer
from src.cl.issue_queue import IssueQueue
from src.cl.alu import ALU

from pymtl3.stdlib.basic_rtl.registers import RegEnRst
from pymtl3.stdlib.basic_rtl.register_files import RegisterFile


class RampCore(Component):
    def construct(s):
        # (1,2) FRONT END - reads from memory and outputs micro ops
        s.front_end = FrontEnd()

        # pipline register - between front end and back end
        s.pipeline_reg_1 = RegEnRst(DualMicroOp)
        s.pipeline_reg_1.in_ //= s.front_end.dual_uop

        # BACK END - executes the micro ops
        # (3) dispatch - sends microops to ROB, and correct execution path
        s.dispatch = Dispatch()
        s.dispatch.in_ //= s.pipeline_reg_1.out

        # reorder buffer - stores microops so they can be committed in order
        s.reorder_buffer = ReorderBuffer()
        s.reorder_buffer.write_in //= s.dispatch.to_rob
        s.reorder_buffer.op_complete //= 0
        s.reorder_buffer.rob_tail //= s.dispatch.rob_idx

        # (4) issue queues - store microops until they are ready to be issued
        s.int_issue_queue = IssueQueue()
        s.int_issue_queue.uop_in //= s.dispatch.to_int_issue
        s.int_issue_queue.busy_table //= s.dispatch.busy_table

        # pipeline regiater - between issue queues and register files
        s.pipeline_reg_2 = RegEnRst(MicroOp)
        s.pipeline_reg_2.in_ //= s.int_issue_queue.uop_out

        # register file - physical registers
        s.register_file = RegisterFile(
            mk_bits(32), nregs=NUM_PHYS_REGS, rd_ports=2, wr_ports=1, const_zero=True
        )
        s.register_file.raddr[0] //= s.pipeline_reg_2.out.prs1
        s.register_file.raddr[1] //= s.pipeline_reg_2.out.prs2

        # (5) execution units - execute the microops TODO:handle immediates
        s.alu = ALU()
        s.alu.a //= s.register_file.rdata[0]
        s.alu.b //= s.register_file.rdata[1]
        s.alu.op //= s.pipeline_reg_2.out.fu_op

        #

        @update
        def update_cntrl():
            s.pipeline_reg_1.en @= ~s.reset
            s.pipeline_reg_2.en @= ~s.reset
