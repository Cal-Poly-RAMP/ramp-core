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
    trunc,
)

from src.cl.dram import DRAM
from src.cl.decode import ROB_ADDR_WIDTH
from src.cl.buffers import MultiInputRdyCircularBuffer
from pymtl3.stdlib.ifcs import RecvIfcRTL, SendIfcRTL


class MemoryUnit(Component):
    def construct(
        s, queue_size=16, memory_size=256, window_size=2, reset_value=0, data=None
    ):
        # checking that addresses work
        assert memory_size < (2**32)

        # from dispatch
        s.allocate_in = RecvIfcRTL(clog2(queue_size) + 1)
        s.update_in = [
            RecvIfcRTL(LoadStoreEntry) for _ in range(window_size)
        ]
        s.load_out = SendIfcRTL(LoadEntry)  # to ROB

        # load store buffer (FIFO for now)
        s.ls_queue = MultiInputRdyCircularBuffer(
            LoadStoreEntry,
            size=queue_size,
            num_inports=window_size,
        )
        s.ls_queue.allocate_in //= s.allocate_in
        for i in range(window_size):
            s.ls_queue.update_in[i] //= s.update_in[i]

        # standin for memory controller
        s.dram = DRAM(
            mk_bits(32),
            num_entries=memory_size,
            rd_ports=1,
            wr_ports=1,
            reset_value=reset_value,
            data=data,
        )

        @update
        def connect_():
            # connecting input to queue
            s.ls_queue.out.rdy @= 1

            # connecting memory to queue
            s.dram.raddr[0] @= trunc(s.ls_queue.out.msg.addr, clog2(memory_size))
            s.dram.waddr[0] @= trunc(s.ls_queue.out.msg.addr, clog2(memory_size))
            s.dram.wdata[0] @= s.ls_queue.out.msg.data
            s.dram.wen[0] @= s.ls_queue.out.msg.optype == STORE

            # connecting memory to load output
            s.load_out.msg.data @= s.dram.rdata[0]
            s.load_out.en @= s.ls_queue.out.msg.optype == LOAD

    def line_trace(s):
        return s.dram.line_trace() + "\n\n" + s.ls_queue.line_trace()


# to ROB
@bitstruct
class LoadEntry:
    data: mk_bits(32)
    rob_idx: mk_bits(ROB_ADDR_WIDTH)

LOAD = 0
STORE = 1

@bitstruct
class LoadStoreEntry:
    optype: mk_bits(1)  # 0 for load, 1 for store
    addr: mk_bits(32)
    data: mk_bits(32)
    rob_idx: mk_bits(ROB_ADDR_WIDTH)