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
from src.cl.icache import ICache

PC_WIDTH = 8
INSTR_WIDTH = 32

# The fetch stage of the pipeline, responsible for fetching instructions and
# branch prediction.
class FetchStage(Component):
    def construct(s):
        # Defining ICache Components
        s.icache = ICache(addr_width=PC_WIDTH, word_width=2 * INSTR_WIDTH)
        s.icache_data = Wire(s.icache.word_width)
        s.pc = OutPort(PC_WIDTH)  # program counter
        s.pc_next = Wire(PC_WIDTH)  # program counter next mux

        # Interface (fetch packet)
        s.fetch_packet = OutPort(FetchPacket)

        @update_ff
        def on_tick():
            # updating pc
            if s.reset:
                s.pc <<= 0
            else:
                s.pc <<= s.pc_next

        @update
        def combi():
            s.pc_next @= s.pc + 8  # TODO: branch prediction
            s.icache_data @= s.icache.read_word(s.pc)
            s.fetch_packet @= FetchPacket(
                inst1=s.icache_data[INSTR_WIDTH : 2 * INSTR_WIDTH],
                inst2=s.icache_data[0:INSTR_WIDTH],
                pc=s.pc,
                valid=1,
            )

    def line_trace(s):
        return "PC: {}".format(s.pc) + "\n" + s.icache.line_trace()


@bitstruct
class FetchPacket:
    pc: mk_bits(PC_WIDTH)
    inst1: mk_bits(32)
    inst2: mk_bits(32)
    valid: mk_bits(1)
