# The ReOrder Buffer
# TODO: there can be much optimization to make smaller.
# TODO: NOT SYNTHESIZEABLE
# We are going to store full microops in the ROB, but for synthesis, only certain
# fields are needed.
from pymtl3 import (
    Bits,
    Bits1,
    Component,
    InPort,
    OutPort,
    Wire,
    bitstruct,
    mk_bits,
    sext,
    update,
    update_ff,
    clog2,
)

from src.cl.decode import ROB_ADDR_WIDTH, ROB_SIZE, DualMicroOp
from src.cl.fetch_stage import PC_WIDTH
from src.cl.register_rename import ISA_REG_BITWIDTH, PHYS_REG_BITWIDTH

from src.cl.dram import DRAM
from src.cl.decode import ROB_ADDR_WIDTH
from src.cl.buffers import MultiInputRdyCircularBuffer
from pymtl3.stdlib.ifcs import RecvIfcRTL, SendIfcRTL


class ReorderBuffer(Component):
    def construct(s, buffer_size=16, window_size=2):
        # from dispatch
        s.allocate_in = RecvIfcRTL(clog2(buffer_size) + 1)

        # from execute
        s.update_in = [RecvIfcRTL(ROBEntryUop) for _ in range(window_size)]
        s.commit_out = SendIfcRTL(ROBEntryUop)  # to commit unit

        # information
        s.bank_full = OutPort()
        s.bank_empty = OutPort()
        s.rob_tail = OutPort(ROB_ADDR_WIDTH)
        s.n_elements = OutPort(clog2(buffer_size) + 1)

        # reorder buffer
        s.buffer = MultiInputRdyCircularBuffer(
            ROBEntryUop,
            size=buffer_size,
            num_inports=window_size,
        )
        s.commit_out //= s.buffer.out
        s.buffer.allocate_in //= s.allocate_in
        # s.buffer.out.rdy //= Bits(1, 1)
        for i in range(window_size):
            s.buffer.update_in[i] //= s.update_in[i]

        @update
        def updt():
            s.buffer.out.rdy @= 1

    def line_trace(s):
        return s.ls_queue.line_trace()


@bitstruct
class ROBEntryUop:
    optype: mk_bits(3)
    prd: mk_bits(PHYS_REG_BITWIDTH)
    stale: mk_bits(PHYS_REG_BITWIDTH)
    data: mk_bits(32)
    rob_idx: mk_bits(ROB_ADDR_WIDTH)
