from pymtl3 import Component, OutPort, update
from pymtl3.stdlib.basic_rtl.registers import RegEnRst
from src.cl.decoder import Decode, DualMicroOp
from src.cl.fetch_stage import FetchStage, FetchPacket


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
        s.decoder = Decode()
        s.decoder.fetch_packet //= s.pipeline_reg_fetch_decode.out

        s.dual_uop = OutPort(DualMicroOp)
        s.dual_uop //= s.decoder.dual_uop

        @update
        def update_cntrl():
            s.pipeline_reg_fetch_decode.en @= ~s.reset

    def line_trace(s):
        return (
            "Fetch Stage: "
            + s.fetch_stage.line_trace()
            + "\nPipeline Register: "
            + s.pipeline_reg_fetch_decode.line_trace()
            + "\nDecoder: "
            + s.decoder.line_trace()
        )
