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
)

from pymtl3.stdlib.ifcs import RecvIfcRTL, SendIfcRTL

# A circular FIFO buffer with multiple input ports.
# The buffer allocates empty spaces on demand, then updates the data later
# Each item has a ready bit, that is set when the data is updated
# Buffer pops off the first item if it is ready

class MultiInputRdyCircularBuffer(Component):
    # TODO: Out of order loads, in order stores
    def construct(s, Type, size=16, num_inports=2):
        s.push_in = [RecvIfcRTL(Type) for _ in range(num_inports)]
        s.rdy_in = [RecvIfcRTL(clog2(size)) for _ in range(num_inports * 2)]
        s.out = SendIfcRTL(Type)
        s.out_next = Wire(Type)
        s.out_en_next = Wire()

        s.buffer = [Wire(Type) for _ in range(size)]
        s.buffer_rdy = [Wire() for _ in range(size)]
        # for appending to the end of the buffer
        s.buffer_append_next = [Wire(Type) for _ in range(num_inports)]
        s.buffer_append_next_en = [Wire() for _ in range(num_inports)]

        s.tail = OutPort(clog2(size))
        s.tail_next = Wire(clog2(size))
        s.head = Wire(clog2(size))
        s.head_next = Wire(clog2(size))

        s.full = Wire()
        s.full_next = Wire()

        s.empty = Wire()
        s.empty_next = Wire()

        @update
        def updt_comb():
            # reset
            if s.reset:
                s.out_next @= 0
                s.head_next @= 0
                s.tail_next @= 0
                s.full_next @= 0
                s.empty_next @= 1
                for i in range(num_inports):
                    s.buffer_append_next_en[i] @= 0
            else:
                s.out_next @= 0
                s.head_next @= s.head
                s.tail_next @= s.tail
                for i in range(num_inports):
                    s.buffer_append_next_en[i] @= 0

                # If an element is popped off stack (output ready and head valid)
                s.out_en_next @= 0
                if (s.out.rdy == 1) & ~s.empty:
                    if s.buffer_rdy[s.head] == 1:
                        s.out_next @= s.buffer[s.head]
                        s.out_en_next @= 1
                        s.head_next @= s.head_next + 1
                        s.full_next @= 0
                        s.empty_next @= s.tail_next == s.head_next
                    # forwarding rdy inputs
                    else:
                        for i in range(num_inports * 2):
                            if (s.rdy_in[i].en == 1) & (s.rdy_in[i].msg == s.head):
                                s.out_next @= s.buffer[s.head]
                                s.out_en_next @= 1
                                s.head_next @= s.head_next + 1
                                s.full_next @= 0
                                s.empty_next @= s.tail_next == s.head_next

                # If elements added to stack
                c = 0
                if ~s.full:
                    for i in range(num_inports):
                        if (s.push_in[i].en == 1):
                            s.buffer_append_next[c] @= s.push_in[i].msg
                            s.buffer_append_next_en[c] @= 1
                            s.tail_next @= s.tail_next + 1
                            s.empty_next @= 0
                            s.full_next @= s.tail_next == s.head_next
                            c = c + 1

        @update_ff
        def updt_ff():
            # reset
            if s.reset:
                for i in range(num_inports):
                    s.buffer_rdy[i] <<= 0

            # Appending new elements to buffer and setting ready bits according to input
            for i in range(num_inports):
                if s.buffer_append_next_en[i] == 1:
                    s.buffer[s.tail + i] <<= s.buffer_append_next[i]
                    s.buffer_rdy[s.tail + i] <<= 0

            # updating rdy signals
            for i in range(num_inports * 2):
                if s.rdy_in[i].en == 1:
                    s.buffer_rdy[s.rdy_in[i].msg] <<= 1

            # updating state
            s.tail <<= s.tail_next
            s.head <<= s.head_next
            s.full <<= s.full_next
            s.empty <<= s.empty_next
            s.out.msg <<= s.out_next
            s.out.en <<= s.out_en_next

    def line_trace(s):
        return (
            f"buffer: {[str(e) for e in s.buffer]}\n"
            f"buffer_next: {[str(e) for e in s.buffer_append_next]}\n"
            f"buffer_append_next_en: {[str(e) for e in s.buffer_append_next_en]}\n"
            f"buffer_rdy: {[str(e) for e in s.buffer_rdy]}\n"
            f"head: {s.head} tail: {s.tail}\n"
            f"in: {[e.msg.uint() if e.en else '-' for e in s.push_in]}"
            f"\nout: {s.out.msg.uint() if s.out.en else '-'}\n"
            f"full: {s.full} empty: {s.empty}\n"
            f"full_next: {s.full_next} empty_next: {s.empty_next}\n"
        )