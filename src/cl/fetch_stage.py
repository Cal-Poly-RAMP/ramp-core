from pymtl3 import (
    Bits,
    Component,
    OutPort,
    Wire,
    bitstruct,
    update,
    update_ff,
    mk_bits,
)
from pymtl3.stdlib.ifcs import RecvIfcRTL, SendIfcRTL
from src.cl.icache import ICache

from src.common.interfaces import BranchUpdate, FetchPacket
from src.common.consts import (
    ICACHE_ADDR_WIDTH,
    INSTR_WIDTH,
)

# The fetch stage of the pipeline, responsible for fetching instructions and
# branch prediction.
class FetchStage(Component):
    def construct(s):
        # Defining ICache Components
        s.icache = ICache(addr_width=ICACHE_ADDR_WIDTH, word_width=2 * INSTR_WIDTH)
        s.icache_data = Wire(s.icache.word_width)
        s.pc = OutPort(32)  # program counter
        s.pc_next = Wire(32)  # program counter next mux

        # Interface (fetch packet)
        s.fetch_packet = OutPort(FetchPacket)

        # Getting mispredict redirect
        s.br_update = RecvIfcRTL(BranchUpdate)
        s.br_update.rdy //= Bits(1, 1)

        @update_ff
        def on_tick():
            # updating pc
            if s.reset:
                s.pc <<= 0
            else:
                s.pc <<= s.pc_next

        @update
        def combi():
            if ~s.br_update.msg.mispredict | ~s.br_update.en:
                s.pc_next @= s.pc + 8  # TODO: branch prediction
            else:
                s.pc_next @= s.br_update.msg.target

            s.icache_data @= s.icache.read_word(s.pc)
            s.fetch_packet @= FetchPacket(
                inst1=s.icache_data[INSTR_WIDTH : 2 * INSTR_WIDTH],
                inst2=s.icache_data[0:INSTR_WIDTH],
                pc=s.pc,
                branch_taken=0,  # TODO: branch prediction
                valid=1,
            )

    def line_trace(s):
        return "PC: {}".format(s.pc) + "\n" + s.icache.line_trace()
