from pymtl3 import Component, InPort, OutPort, bitstruct, update, mk_bits
from src.cl.decode import (
    DualMicroOp,
    MicroOp,
    NO_OP,
    INT_ISSUE_UNIT,
    MEM_ISSUE_UNIT,
    ROB_ADDR_WIDTH,
)


class Dispatch(Component):
    def construct(s):
        # Interface (dual uops in, dual uops out)
        s.in_ = InPort(DualMicroOp)
        s.rob_idx = InPort(ROB_ADDR_WIDTH)  # for updating uops with ROB index
        s.to_rob = OutPort(DualMicroOp)  # for adding microops to ROB

        s.to_int_issue = OutPort(DualMicroOp)  # for adding microops to int issue queue
        s.to_mem_issue = OutPort(DualMicroOp)  # for adding microops to mem issue queue

        s.uop1_dispatch = SingleDispatch()
        s.uop1_dispatch.in_ //= s.in_.uop1
        s.to_rob.uop1 //= s.uop1_dispatch.to_rob
        s.to_int_issue.uop1 //= s.uop1_dispatch.to_int_issue
        s.to_mem_issue.uop1 //= s.uop1_dispatch.to_mem_issue

        s.uop2_dispatch = SingleDispatch()
        s.uop2_dispatch.in_ //= s.in_.uop2
        s.to_rob.uop2 //= s.uop2_dispatch.to_rob
        s.to_int_issue.uop2 //= s.uop2_dispatch.to_int_issue
        s.to_mem_issue.uop2 //= s.uop2_dispatch.to_mem_issue

        @update
        def update_rob_idx():
            s.uop1_dispatch.rob_idx @= s.rob_idx
            s.uop2_dispatch.rob_idx @= s.rob_idx + 1

    def line_trace(s):
        return (
            f"in: {s.in_}\n"
            f"to_int_issue: {s.uop1_dispatch.in_}\n"
            f"to_mem_issue: {s.uop2_dispatch.in_}\n"
        )


class SingleDispatch(Component):
    def construct(s):
        # Interface (dual uops in, dual uops out)
        s.in_ = InPort(MicroOp)
        s.rob_idx = InPort(ROB_ADDR_WIDTH)  # for updating uops with ROB index
        s.to_rob = OutPort(MicroOp)  # for adding microops to ROB
        s.to_rob //= s.in_

        s.to_int_issue = OutPort(MicroOp)  # for adding microops to int issue queue
        s.to_mem_issue = OutPort(MicroOp)  # for adding microops to mem issue queue

        @update
        def issue():
            if s.in_.issue_unit == INT_ISSUE_UNIT:
                s.to_int_issue @= s.in_
                s.to_int_issue.rob_idx @= s.rob_idx
            else:
                s.to_int_issue @= NO_OP
            if s.in_.issue_unit == MEM_ISSUE_UNIT:
                s.to_mem_issue @= s.in_
                s.to_mem_issue.rob_idx @= s.rob_idx
            else:
                s.to_mem_issue @= NO_OP
