from pymtl3 import (
    Bits,
    Component,
    OutPort,
    Wire,
    bitstruct,
    update,
    update_ff,
    mk_bits,
    trunc,
    clog2,
    InPort,
    concat,
)
from pymtl3.stdlib.ifcs import RecvIfcRTL, SendIfcRTL
from pymtl3.stdlib.mem.ROMRTL import CombinationalROMRTL

from src.common.interfaces import BranchUpdate, FetchPacket
from src.common.consts import (
    ICACHE_ADDR_WIDTH,
    ICACHE_SIZE,
    INSTR_WIDTH,
)

# The fetch stage of the pipeline, responsible for fetching instructions and
# branch prediction.
class FetchStage(Component):
    def construct(s, data, size=ICACHE_SIZE, window_size=2):
        # Defining ICache Components
        # s.icache = ICache(addr_width=ICACHE_ADDR_WIDTH, word_width=2 * INSTR_WIDTH)
        s.icache = CombByteAddrROMRTL(
            num_entries=size,
            bpw=8,
            data=data,
            num_ports=1
        )

        # Program counters
        s.pc = OutPort(32)
        s.pc_next = Wire(32)

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

            # calculating input address (converting from byte addr to word addr)
            s.icache.raddr[0] @= trunc(s.pc, clog2(size))

            s.fetch_packet @= FetchPacket(
                inst1=s.icache.rdata[0][0:INSTR_WIDTH],
                inst2=s.icache.rdata[0][INSTR_WIDTH : window_size * INSTR_WIDTH],
                pc=s.pc,
                branch_taken=0,  # TODO: branch prediction
                valid=1,
            )

    def line_trace(s):
        return "PC: {}".format(s.pc) + "\n" + s.icache.line_trace()

class CombByteAddrROMRTL( Component ):

  def construct( s, num_entries, bpw, data, num_ports=1 ):
    assert len(data) == num_entries

    s.raddr = [ InPort( clog2(num_entries) ) for _ in range(num_ports) ]
    s.rdata = [ OutPort( mk_bits(8 * bpw) ) for _ in range(num_ports) ]

    s.mem = [ Wire( mk_bits(8) ) for _ in range(num_entries) ]
    for i in range(num_entries):
      s.mem[i] //= data[i]

    @update
    def up_read_rom():
      for i in range(num_ports):
        s.rdata[i] @= concat(*s.mem[ s.raddr[i] : s.raddr[i] + bpw ][::-1])