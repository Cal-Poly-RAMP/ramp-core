from pymtl3 import (
    Component,
    InPort,
    OutPort,
    Wire,
    clog2,
    update_ff,
    update,
    zext,
    Bits,
)
from src.cl.register_rename import NUM_PHYS_REGS
from src.cl.decode import (
    B_TYPE,
    I_TYPE,
    INT_ISSUE_UNIT,
    J_TYPE,
    NO_OP,
    R_TYPE,
    S_TYPE,
    U_TYPE,
    DualMicroOp,
    MicroOp,
)

ISSUE_QUEUE_DEPTH = 16


class IssueQueue(Component):
    def construct(s):
        # uop to be added to queue from dispatch
        s.duop_in = InPort(DualMicroOp)
        # busy table from register rename for determining when ready to issued
        s.busy_table = InPort(NUM_PHYS_REGS)
        # uop to be executed from queue
        # TODO: change to only necessary data rather than entire uop
        s.uop_out = OutPort(MicroOp)

        # issue queue - implemented as a collapsing queue
        s.queue = [Wire(MicroOp) for _ in range(ISSUE_QUEUE_DEPTH)]
        s.tail = Wire(clog2(ISSUE_QUEUE_DEPTH))

        # status
        s.queue_full = OutPort()
        s.queue_empty = OutPort()

        # @update
        # def comb():
        #     # s.queue_empty @= s.tail == 0

        @update_ff
        def ff():
            if s.reset:
                s.tail <<= 0
                s.queue_full <<= 0
                s.queue_empty <<= 1
                # TODO: reset queue

            # ISSUING uops from queue, if ready
            collapse = 0
            for i in range(ISSUE_QUEUE_DEPTH):
                # if instruction has already been issued, collapse queue to fill in
                if collapse:
                    s.queue[i - 1] <<= s.queue[i]
                # if not busy and valid, issue
                elif s.queue[i].valid:
                    # r,s,b type: need rs1, rs2 to be not busy
                    if (
                        (s.queue[i].optype == R_TYPE)
                        | (s.queue[i].optype == S_TYPE)
                        | (s.queue[i].optype == B_TYPE)
                    ):
                        if (
                            ~s.busy_table[s.queue[i].prs1]
                            & ~s.busy_table[s.queue[i].prs2]
                        ):
                            s.uop_out <<= s.queue[i]
                            s.tail <<= s.tail - 1
                            s.queue_full <<= 0
                            collapse = 1

                    # i type: need rs1 to be not busy
                    elif s.queue[i].optype == I_TYPE:
                        if ~s.busy_table[s.queue[i].prs1]:
                            s.uop_out <<= s.queue[i]
                            s.tail <<= s.tail - 1
                            s.queue_full <<= 0
                            collapse = 1

                    # u,b,j type: ready to issue
                    elif (s.queue[i].optype == U_TYPE) | (s.queue[i].optype == J_TYPE):
                        s.uop_out <<= s.queue[i]
                        s.tail <<= s.tail - 1
                        s.queue_full <<= 0
                        collapse = 1

            if collapse:
                s.queue_empty <<= (s.tail - 1) == 0
                s.queue[ISSUE_QUEUE_DEPTH - 1] <<= MicroOp(
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                )

            # APPENDING new uops to queue, if valid
            if (
                s.duop_in.uop1.valid
                & s.duop_in.uop2.valid
                & (s.tail < (ISSUE_QUEUE_DEPTH - 1))
            ):
                s.queue[s.tail] <<= s.duop_in.uop1
                s.queue[s.tail + 1] <<= s.duop_in.uop2

                #  if overflow, no wrap around
                s.queue_empty <<= 0
                s.tail <<= s.tail + 2
                if s.tail + 2 == 0:
                    s.queue_full <<= 1

            elif s.duop_in.uop1.valid & ~s.queue_full:
                s.queue[s.tail] <<= s.duop_in.uop1

                s.queue_empty <<= 0
                s.tail <<= s.tail + 1
                if s.tail + 1 == 0:
                    s.queue_full <<= 1

            elif s.duop_in.uop2.valid & ~s.queue_full:
                s.queue[s.tail] <<= s.duop_in.uop2

                s.queue_empty <<= 0
                s.tail <<= s.tail + 1
                if s.tail + 1 == 0:
                    s.queue_full <<= 1

    def line_trace(s):
        return (
            f"Issue Queue: {[i.to_bits().uint() for i in s.queue]}\n"
            f"\tTail: {s.tail}\n"
            f"\tduop In: {s.duop_in.uop1}\n\t\t{s.duop_in.uop2}\n"
            f"\tuop Out: {s.uop_out}\n"
            f"\tQueue Full: {s.queue_full}\n"
            f"\tQueue Empty: {s.queue_empty}\n"
            f"\tBusy Table: {s.busy_table}"
        )
