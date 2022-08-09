from pymtl3 import Component, InPort, OutPort, Wire, clog2, update_ff, update, zext
from src.cl.register_rename import NUM_PHYS_REGS
from src.cl.decoder import INT_ISSUE_UNIT, NO_OP, DualMicroOp, MicroOp

INT_ISSUE_DEPTH = 16

class IssueQueue(Component):
    def construct(s):
        # uop to be added to queue from dispatch
        s.uop_in = InPort(DualMicroOp)
        # busy table from register rename for determining when ready to issued
        s.busy_table = InPort(NUM_PHYS_REGS)
        # uop to be executed from queue
        # TODO: change to only necessary data rather than entire uop
        s.uop_out = OutPort(MicroOp)

        # issue queue - implemented as a circular buffer
        s.queue = [Wire(MicroOp) for _ in range(INT_ISSUE_DEPTH)]
        s.head = Wire(clog2(INT_ISSUE_DEPTH))
        s.tail = Wire(clog2(INT_ISSUE_DEPTH))

        @update
        def comb():
            # add uop to queue if it is not full
            pass


        @update_ff
        def ff():
            # reset
            if s.reset:
                s.head <<= 0
                s.tail <<= 0
                for i in range(INT_ISSUE_DEPTH):
                    s.queue[i] <<= NO_OP

    def line_trace(s):
        return (f"Issue Queue: {[i for i in s.queue]}",
                f"Head: {s.head}",
                f"Tail: {s.tail}"
                f"Uop In: {s.uop_in}",
                f"Uop Out: {s.uop_out}")