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
    zext,
    sext,
)

from src.cl.dram import DRAM
from src.common.consts import (
    MEM_LOAD,
    MEM_Q_SIZE,
    MEM_STORE,
    ROB_SIZE,
    MEM_FLAG,
    WINDOW_SIZE,
    MEM_SW,
    MEM_SH,
    MEM_SB,
    MEM_LW,
    MEM_LH,
    MEM_LB,
    MEM_LBU,
    MEM_LHU,
)
from src.common.interfaces import IOEntry
from src.cl.buffers import MultiInputRdyCircularBuffer
from pymtl3.stdlib.ifcs import RecvIfcRTL, SendIfcRTL

class MemoryUnit(Component):
    def construct(
        s, queue_size=16, memory_size=256, window_size=2, reset_value=0, mmio_start=0x11000000, mmio_size=0xff
    ):
        # checking that addresses work
        assert memory_size < (2**32)

        # from dispatch
        s.allocate_in = RecvIfcRTL(WINDOW_SIZE)
        s.update_in = [RecvIfcRTL(LoadStoreEntry) for _ in range(window_size)]
        s.load_out = SendIfcRTL(LoadEntry)  # to ROB
        s.mem_q_tail = OutPort(clog2(MEM_Q_SIZE))
        # MMIO
        s.io_bus_out = SendIfcRTL(IOEntry)
        s.io_bus_in = RecvIfcRTL(IOEntry)

        # load store buffer (FIFO for now)
        s.ls_queue = MultiInputRdyCircularBuffer(
            LoadStoreEntry,
            size=queue_size,
            num_inports=window_size,
        )
        s.mem_q_tail //= s.ls_queue.tail
        for i in range(window_size):
            s.ls_queue.update_in[i] //= s.update_in[i]
            s.ls_queue.update_idx_in[i].msg //= s.update_in[i].msg.mem_q_idx
            s.ls_queue.update_idx_in[i].en //= s.update_in[i].en

        # standin for memory controller
        s.dram = DRAM(
            mk_bits(32),
            num_entries=memory_size,
            rd_ports=1,
            wr_ports=1,
            reset_value=reset_value,
        )

        queue_addr_nbits = clog2(queue_size) + 1
        mem_addr_nbits = clog2(memory_size)

        @update
        def connect_():
            # defaults
            s.io_bus_out.msg.addr @= 0
            s.io_bus_out.msg.data @= 0
            s.io_bus_out.en @= 0
            s.io_bus_in.rdy @= 1

            s.load_out.msg.data @= 0
            s.load_out.msg.rob_idx @= 0
            s.load_out.en @= 0

            s.dram.raddr[0] @= 0
            s.dram.waddr[0] @= 0
            s.dram.wdata[0] @= 0
            s.dram.wen[0] @= 0

            # connecting input to queue
            s.ls_queue.out.rdy @= 1
            s.ls_queue.allocate_in.msg @= zext(s.allocate_in.msg, queue_addr_nbits)
            s.ls_queue.allocate_in.en @= s.allocate_in.en
            s.allocate_in.rdy @= s.ls_queue.allocate_in.rdy

            # connecting MMIO to queue (in-order)
            if (s.ls_queue.out.msg.addr >= mmio_start) & (s.ls_queue.out.msg.addr < (mmio_start + mmio_size)):
                # connecting MMIO output from queue store
                s.io_bus_out.msg @= IOEntry(s.ls_queue.out.msg.addr, s.ls_queue.out.msg.data)
                s.io_bus_out.en @= s.ls_queue.out.en & (
                    ((s.ls_queue.out.msg.op & MEM_FLAG) == MEM_STORE)
                )

                # connecting MMIO input from queue load
                # TODO: need to wait for input to be enabled
                if s.ls_queue.out.msg.op == MEM_LW:
                    s.load_out.msg.data @= s.io_bus_in.msg.data
                elif s.ls_queue.out.msg.op == MEM_LH:
                    s.load_out.msg.data @= sext(s.io_bus_in.msg.data[0:16], 32)
                elif s.ls_queue.out.msg.op == MEM_LHU:
                    s.load_out.msg.data @= zext(s.io_bus_in.msg.data[0:16], 32)
                elif s.ls_queue.out.msg.op == MEM_LB:
                    s.load_out.msg.data @= sext(s.io_bus_in.msg.data[0:8], 32)
                elif s.ls_queue.out.msg.op == MEM_LBU:
                    s.load_out.msg.data @= zext(s.io_bus_in.msg.data[0:8], 32)
                else:
                    s.load_out.msg.data @= s.io_bus_in.msg.data

                s.load_out.msg.rob_idx @= s.ls_queue.out.msg.rob_idx
                s.load_out.en @= s.ls_queue.out.en & (
                    ((s.ls_queue.out.msg.op & MEM_FLAG) == MEM_LOAD)
                )
                s.io_bus_in.rdy @= s.load_out.rdy

            # connecting DRAM to queue
            else:
                # connecting dram output from queue store
                s.dram.raddr[0] @= trunc(s.ls_queue.out.msg.addr, mem_addr_nbits)
                s.dram.waddr[0] @= trunc(s.ls_queue.out.msg.addr, mem_addr_nbits)
                # slicing and signing happens in execution
                s.dram.wdata[0] @= s.ls_queue.out.msg.data

                s.dram.wen[0] @= s.ls_queue.out.en & (
                    (s.ls_queue.out.msg.op & MEM_FLAG) == MEM_STORE
                )

                # connecting dram input from queue load
                if s.ls_queue.out.msg.op == MEM_LW:
                    s.load_out.msg.data @= s.dram.rdata[0]
                elif s.ls_queue.out.msg.op == MEM_LH:
                    s.load_out.msg.data @= sext(s.dram.rdata[0][0:16], 32)
                elif s.ls_queue.out.msg.op == MEM_LHU:
                    s.load_out.msg.data @= zext(s.dram.rdata[0][0:16], 32)
                elif s.ls_queue.out.msg.op == MEM_LB:
                    s.load_out.msg.data @= sext(s.dram.rdata[0][0:8], 32)
                elif s.ls_queue.out.msg.op == MEM_LBU:
                    s.load_out.msg.data @= zext(s.dram.rdata[0][0:8], 32)
                else:
                    s.load_out.msg.data @= s.dram.rdata[0]

                s.load_out.msg.rob_idx @= s.ls_queue.out.msg.rob_idx
                s.load_out.en @= s.ls_queue.out.en & (
                    (s.ls_queue.out.msg.op & MEM_FLAG) == MEM_LOAD
                )

    def line_trace(s):
        return s.dram.line_trace() + "\nLoad/Store Buffer\n" + s.ls_queue.line_trace()


# to ROB
@bitstruct
class LoadEntry:
    data: mk_bits(32)
    rob_idx: mk_bits(clog2(ROB_SIZE))

@bitstruct
class LoadStoreEntry:
    op: mk_bits(4)  # same as decode MEM constants
    addr: mk_bits(32)
    data: mk_bits(32)
    rob_idx: mk_bits(clog2(ROB_SIZE))
    mem_q_idx: mk_bits(clog2(MEM_Q_SIZE))

    # def __str__(s):
    #     return "op: {} addr: {} data: {} rob_idx: {} mem_q_idx: {}".format(
    #         s.op, s.addr, s.data, s.rob_idx, s.mem_q_idx
    #     )