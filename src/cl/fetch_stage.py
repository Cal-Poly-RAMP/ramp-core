from pymtl3 import *
from pymtl3 import Bits32
from pymtl3.stdlib import stream

from src.cl.icache import ICache

# The fetch stage of the pipeline, responsible for fetching instructions and
# branch prediction.
class FetchStage(Component):
    def construct(s):
        # Defining ICache Components
        s.icache = ICache()
        s.pc = Wire(s.icache.addr_width)  # program counter
        s.pc_next = Wire(s.icache.addr_width)  # program counter next mux

        # Interface (fetch packet)
        s.send = stream.ifcs.SendIfcRTL(FetchPacket)

        # Queue Adaptor
        s.fetch_buffer = stream.SendQueueAdapter(FetchPacket)
        s.send //= s.fetch_buffer.send

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

        @update_once
        def once():
            s.fetch_buffer.enq(s.icache.read_word(s.pc))


@bitstruct
class FetchPacket(Interface):
    instr1: Bits32
    instr2: Bits32
