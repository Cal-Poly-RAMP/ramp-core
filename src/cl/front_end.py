from pymtl3 import Component, OutPort, update
from pymtl3.stdlib.basic_rtl.registers import RegEnRst

from src.cl.decode import Decode
from src.cl.fetch_stage import FetchStage

from src.common.consts import NUM_PHYS_REGS
from src.common.interfaces import FetchPacket, DualMicroOp


class FrontEnd(Component):
    def construct(s):
        # (1) Fetch stage
        s.fetch_stage = FetchStage()

        # Pipeline register
        s.pipeline_reg_fetch_decode = RegEnRst(
            FetchPacket, reset_value=FetchPacket(0, 0, 0)
        )
        s.pipeline_reg_fetch_decode.in_ //= s.fetch_stage.fetch_packet

        # (2) Decode stage
        s.decode = Decode()
        s.decode.fetch_packet //= s.pipeline_reg_fetch_decode.out

        s.dual_uop = OutPort(DualMicroOp)
        s.dual_uop //= s.decode.dual_uop

        s.busy_table = OutPort(NUM_PHYS_REGS)
        s.busy_table //= s.decode.busy_table

        @update
        def update_cntrl():
            s.pipeline_reg_fetch_decode.en @= ~s.reset

    def line_trace(s):
        return (
            "Fetch Stage: "
            + s.fetch_stage.line_trace()
            + "\nPipeline Register: "
            + s.pipeline_reg_fetch_decode.line_trace()
            + "\ndecode: "
            + s.decode.line_trace()
        )
