from pymtl3 import Component

from cl.decoder import DualMicroOp
from front_end import FrontEnd
from pymtl3.stdlib.basic_rtl.registers import RegEnRst


class RampCore(Component):
    def construct(s):
        # front end - reads from memory and outputs micro ops
        s.front_end = FrontEnd()

        # pipline register - between front end and back end
        s.pipeline_reg_front_end_back_end = RegEnRst(DualMicroOp)

        # back end - executes the micro ops
