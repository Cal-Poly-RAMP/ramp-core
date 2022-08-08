from pymtl3 import Component

from src.cl.decoder import DualMicroOp
from src.cl.front_end import FrontEnd
from src.cl.dispatch import Dispatch
from src.cl.reorder_buffer import ReorderBuffer

from pymtl3.stdlib.basic_rtl.registers import RegEnRst


class RampCore(Component):
    def construct(s):
        # FRONT END - reads from memory and outputs micro ops
        s.front_end = FrontEnd()

        # pipline register - between front end and back end
        s.pipeline_reg_1 = RegEnRst(DualMicroOp)
        s.pipeline_reg_1.in_ //= s.front_end.dual_uop
        s.pipeline_reg_1.en @= 1

        # BACK END - executes the micro ops
        # dispatch - sends microops to ROB, and correct execution path
        s.dispatch = Dispatch()
        s.dispatch.in_ //= s.pipeline_reg_1.out

        # reorder buffer - stores microops so they can be committed in order
        s.reorder_buffer = ReorderBuffer()
        s.reorder_buffer.write_in //= s.dispatch.to_rob
        s.reorder_buffer.op_complete @= 0
        s.reorder_buffer.rob_tail //= s.dispatch.rob_idx

        # issue queues - store microops until they are ready to be issued
