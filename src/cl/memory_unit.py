from pymtl3 import (
    Component,
    Bits,
    mk_bits,
    InPort,
    OutPort,
    Wire,
    clog2,
    update_ff,
    update,
    bitstruct,
)

from src.cl.dram import DRAM
from src.cl.decode import MEM_FUNCT_UNIT, MEM_LOAD, MEM_STORE, MicroOp, MEM_ISSUE_UNIT
from src.cl.buffers import MultiInputRdyCircularBuffer
from pymtl3.stdlib.ifcs import RecvIfcRTL, SendIfcRTL


class MemoryUnit(Component):
    def construct(
        s, queue_size=16, memory_size=256, window_size=2, reset_value=0, data=None
    ):
        # from dispatch
        s.push_in = [RecvIfcRTL(LoadStoreEntry) for _ in range(window_size)]
        s.load_out = SendIfcRTL(LoadEntry)
        s.store_out = SendIfcRTL(StoreEntry)

        # Load Store Buffer (FIFO for now)
        s.ls_queue = MultiInputRdyCircularBuffer(
            LoadStoreEntry,
            size=queue_size,
            num_inports=window_size,
        )
        for i in range(window_size):
            s.ls_queue.push_in[i].en @= s.push_in[i].en
            s.ls_queue.push_in[i].msg @= s.push_in[i].msg
            s.ls_queue.rdy_in[i].en @= s.push_in[i].rdy

        # Standin for memory controller
        s.dram = DRAM(
            Bits(32),
            num_entries=32,
            rd_ports=1,
            wr_ports=1,
            reset_value=reset_value,
            data=data,
        )

        @update
        def push():
            pass

        @update
        def pop():
            pass


@bitstruct
class LoadEntry:
    rdy: mk_bits(1)  # address has been updated by mem function unit
    addr: mk_bits(32)
    rob_idx: mk_bits(32)

    def line_trace(s):
        return f" {s.addr} {s.rob_idx}"

class StoreEntry:
    rdy: mk_bits(1)  # address has been updated by mem function unit
    addr: mk_bits(32)
    data: mk_bits(32)
    rob_idx: mk_bits(32)

    def line_trace(s):
        return f" {s.addr} {s.rob_idx}"

LOAD = 0
STORE = 1

@bitstruct
class LoadStoreEntry:
    optype: mk_bits(1)  # 0 for load, 1 for store
    rdy: mk_bits(1)  # address, data has been updated by mem function unit
    addr: mk_bits(32)
    data: mk_bits(32)
    rob_idx: mk_bits(32)

    def line_trace(s):
        return f"{s.addr} {s.data} {s.rob_idx}"
