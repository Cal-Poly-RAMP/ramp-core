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
    zext,
    trunc,
)

from pymtl3.stdlib.ifcs import RecvIfcRTL, SendIfcRTL

# A circular FIFO buffer with multiple input ports.
# The buffer allocates empty spaces on demand, then updates the data later
# Each item has a ready bit, that is set when the data is updated
# Buffer pops off the first item if it is ready


class MultiInputRdyCircularBuffer(Component):
    # TODO: Out of order loads, in order stores
    def construct(s, Type, size=16, num_inports=2):
        # the number of spaces to allocate (increment the tail)
        s.allocate_in = RecvIfcRTL(clog2(size) + 1)
        # inputs for updating elements in the buffer, data and index
        s.update_in = [RecvIfcRTL(Type) for _ in range(num_inports)]
        s.update_idx_in = [RecvIfcRTL(clog2(size)) for _ in range(num_inports)]
        for i in range(num_inports):
            s.update_in[i].rdy //= Bits(1, 1)
            s.update_idx_in[i].rdy //= Bits(1, 1)

        s.out = SendIfcRTL(Type)
        s.out_next = Wire(Type)
        s.out_en_next = Wire()

        s.buffer = [Wire(Type) for _ in range(size)]
        s.buffer_rdy = [Wire() for _ in range(size)]

        s.tail = OutPort(clog2(size))
        s.tail_next = Wire(clog2(size))
        s.head = Wire(clog2(size))
        s.head_next = Wire(clog2(size))

        s.full = Wire()
        s.empty = Wire()
        s.n_elements = OutPort(clog2(size) + 1)
        s.n_elements_next = Wire(clog2(size) + 1)

        @update
        def updt_comb():
            s.full @= s.n_elements == size
            s.empty @= s.n_elements == 0
            s.allocate_in.rdy @= ~s.full

            # reset
            if s.reset:
                s.out_next @= Type(0)
                s.head_next @= 0
                s.tail_next @= 0
                s.n_elements_next @= 0
            else:
                # default values
                s.out_en_next @= 0
                s.head_next @= s.head
                s.tail_next @= s.tail
                s.n_elements_next @= s.n_elements

                # popping off stack if first element valid
                if s.out.rdy & ~s.empty:
                    # checking head of stack
                    if s.buffer_rdy[s.head]:
                        s.out_next @= s.buffer[s.head]
                        s.out_en_next @= 1
                        s.head_next @= s.head_next + 1
                        s.n_elements_next @= s.n_elements - 1
                    # forwarding update inputs
                    for i in range(num_inports):
                        # ensuring that update data has a corresponding index
                        assert ~(s.update_idx_in[i].en ^ s.update_in[i].en)
                        if s.update_idx_in[i].en & (s.update_idx_in[i].msg == s.head):
                            # checking that index has valid corresponding data
                            s.out_next @= s.update_in[i].msg
                            s.out_en_next @= 1
                            s.head_next @= s.head_next + 1
                            s.n_elements_next @= s.n_elements - 1

                # updating tail with elements allocated
                if s.allocate_in.en == 1:
                    s.tail_next @= trunc(
                        zext(s.tail, clog2(size) + 1) + s.allocate_in.msg, clog2(size)
                    )
                    s.n_elements_next @= s.n_elements_next + zext(
                        s.allocate_in.msg, clog2(size) + 1
                    )

        @update_ff
        def updt_ff():
            # reset
            # TODO: just set the first ready bit to 0?
            if s.reset:
                for i in range(num_inports):
                    s.buffer_rdy[i] <<= 0

            # setting newely allocated elements to 0
            if s.allocate_in.en:
                for i in range(s.allocate_in.msg):
                    s.buffer_rdy[s.tail + i] <<= 0

            # updating data, and setting ready bit
            for i in range(num_inports):
                # ensuring that update data has a corresponding index
                assert ~(s.update_idx_in[i].en ^ s.update_in[i].en), \
                    f"update idx[{i}] en: {s.update_idx_in[i].en}, update[{i}] en: {s.update_in[i].en}"
                if s.update_idx_in[i].en:
                    s.buffer[s.update_idx_in[i].msg] <<= s.update_in[i].msg
                    s.buffer_rdy[s.update_idx_in[i].msg] <<= 1

            # updating state
            s.tail <<= s.tail_next
            s.head <<= s.head_next
            s.out.msg <<= s.out_next
            s.out.en <<= s.out_en_next
            s.n_elements <<= s.n_elements_next

    def line_trace(s):
        return (
            f"buffer: {[str(e) for e in s.buffer]}\n"
            f"buffer_rdy: {[str(e) for e in s.buffer_rdy]}\n"
            f"head: {s.head} tail: {s.tail}\n"
            f"allocate in: {s.allocate_in.msg if s.allocate_in.en else '-'}\n"
            f"update in: {[str(e.msg) for e in s.update_in]}\n"
            f"update idx in: {[str(e.msg) for e in s.update_idx_in]}\n"
            f"out: {s.out.msg.uint() if s.out.en else '-'}\n"
            f"full: {s.full} empty: {s.empty}\n"
            f"n_elements: {s.n_elements.uint()}\n"
        )
