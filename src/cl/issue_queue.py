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
from src.common.consts import (
    B_TYPE,
    I_TYPE,
    INT_ISSUE_UNIT,
    J_TYPE,
    R_TYPE,
    S_TYPE,
    U_TYPE,
    NUM_PHYS_REGS,
    ISSUE_QUEUE_DEPTH,
)
from src.common.interfaces import DualMicroOp, MicroOp, NO_OP


class IssueQueue(Component):
    def construct(s):
        # uop to be added to queue from dispatch
        s.duop_in = InPort(DualMicroOp)
        # busy table from register rename for determining when ready to issued
        s.busy_table = InPort(NUM_PHYS_REGS)
        # uop to be executed from queue
        # TODO: change to only necessary data rather than entire uop
        s.uop_out = OutPort(MicroOp)
        s.uop_out_next = OutPort(MicroOp)

        # issue queue - implemented as a collapsing queue
        s.queue = [Wire(MicroOp) for _ in range(ISSUE_QUEUE_DEPTH)]
        s.queue_next = [Wire(MicroOp) for _ in range(ISSUE_QUEUE_DEPTH)]
        s.tail = Wire(clog2(ISSUE_QUEUE_DEPTH))
        s.tail_next = Wire(clog2(ISSUE_QUEUE_DEPTH))

        # status
        s.queue_full = OutPort()
        s.queue_full_next = OutPort()
        s.queue_empty = OutPort()
        s.queue_empty_next = OutPort()

        @update
        def comb():
            # reset
            collapse = 0
            s.tail_next @= 0
            s.queue_full_next @= 0
            s.queue_empty_next @= 1
            s.uop_out_next @= NO_OP
            for i in range(ISSUE_QUEUE_DEPTH):
                s.queue_next[i] @= NO_OP

            if ~s.reset:
                # APPENDING new uops to queue, if valid
                for i in range(ISSUE_QUEUE_DEPTH):
                    s.queue_next[i] @= s.queue[i]
                s.uop_out_next @= NO_OP
                s.tail_next @= s.tail
                s.queue_full_next @= s.queue_full
                s.queue_empty_next @= s.queue_empty

                if (
                    s.duop_in.uop1.valid
                    & s.duop_in.uop2.valid
                    & (s.tail_next < (ISSUE_QUEUE_DEPTH - 1))
                ):
                    s.queue_next[s.tail_next] @= s.duop_in.uop1
                    s.queue_next[s.tail_next + 1] @= s.duop_in.uop2

                    #  if overflow, no wrap around
                    s.queue_empty_next @= 0
                    s.tail_next @= s.tail_next + 2
                    if s.tail_next == 0:
                        s.queue_full_next @= 1

                elif s.duop_in.uop1.valid & ~s.queue_full:
                    s.queue_next[s.tail_next] @= s.duop_in.uop1

                    s.queue_empty_next @= 0
                    s.tail_next @= s.tail_next + 1
                    if s.tail_next == 0:
                        s.queue_full_next @= 1

                elif s.duop_in.uop2.valid & ~s.queue_full:
                    s.queue_next[s.tail_next] @= s.duop_in.uop2

                    s.queue_empty_next @= 0
                    s.tail_next @= s.tail_next + 1
                    if s.tail_next == 0:
                        s.queue_full_next @= 1

                # ISSUING uops from queue, if ready
                for i in range(ISSUE_QUEUE_DEPTH):
                    # s.queue_next[i] @= s.queue[i]
                    # if instruction has already been issued, collapse queue to fill in
                    if collapse:
                        s.queue_next[i - 1] @= s.queue_next[i]
                    # if not busy and valid, issue
                    elif s.queue_next[i].valid:
                        # r,s,b type: need rs1, rs2 to be not busy
                        if (
                            (s.queue_next[i].optype == R_TYPE)
                            | (s.queue_next[i].optype == S_TYPE)
                            | (s.queue_next[i].optype == B_TYPE)
                        ):
                            if (
                                ~s.busy_table[s.queue_next[i].prs1]
                                & ~s.busy_table[s.queue_next[i].prs2]
                            ):
                                s.uop_out_next @= s.queue_next[i]
                                s.tail_next @= s.tail_next - 1
                                s.queue_full_next @= 0
                                collapse = 1

                        # i type: need rs1 to be not busy
                        elif s.queue_next[i].optype == I_TYPE:
                            if ~s.busy_table[s.queue_next[i].prs1]:
                                s.uop_out_next @= s.queue_next[i]
                                s.tail_next @= s.tail_next - 1
                                s.queue_full_next @= 0
                                collapse = 1

                        # u,b,j type: ready to issue
                        elif (s.queue_next[i].optype == U_TYPE) | (
                            s.queue_next[i].optype == J_TYPE
                        ):
                            s.uop_out_next @= s.queue_next[i]
                            s.tail_next @= s.tail_next - 1
                            s.queue_full_next @= 0
                            collapse = 1

                if collapse:
                    s.queue_empty_next @= (s.tail_next - 1) == 0
                    s.queue_next[ISSUE_QUEUE_DEPTH - 1] @= NO_OP

        @update_ff
        def ff():
            s.tail <<= s.tail_next
            s.queue_full <<= s.queue_full_next
            s.queue_empty <<= s.queue_empty_next
            s.uop_out <<= s.uop_out_next
            for i in range(ISSUE_QUEUE_DEPTH):
                s.queue[i] <<= s.queue_next[i]

    def line_trace(s):
        return (
            f"\n\tIssue Queue: {[str(i.inst) if i else 0 for i in s.queue ]}\n"
            f"\tTail: {s.tail}\n"
            f"\tduop In: {s.duop_in.uop1}\n\t\t{s.duop_in.uop2}\n"
            f"\tuop Out: {s.uop_out}\n"
            f"\tQueue Full: {s.queue_full}\n"
            f"\tQueue Empty: {s.queue_empty}\n"
        )
