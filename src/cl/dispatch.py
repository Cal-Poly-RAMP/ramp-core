from pymtl3 import Component, InPort, OutPort, update, mk_bits, zext, clog2
from src.common.interfaces import DualMicroOp, MicroOp, NO_OP
from src.common.consts import (
    BRANCH_FUNCT_UNIT,
    MEM_Q_SIZE,
    INT_ISSUE_UNIT,
    MEM_ISSUE_UNIT,
    ROB_SIZE,
)


class Dispatch(Component):
    def construct(s):
        # Interface (dual uops in, dual uops out)
        s.in_ = InPort(DualMicroOp)
        s.rob_idx = InPort(clog2(ROB_SIZE))  # for updating uops with ROB index
        s.mem_q_tail = InPort(clog2(MEM_Q_SIZE))
        s.to_rob = OutPort(DualMicroOp)  # for adding microops to ROB

        s.to_int_issue = OutPort(DualMicroOp)  # for adding microops to int issue queue
        s.to_mem_issue = OutPort(DualMicroOp)  # for adding microops to mem issue queue
        s.to_branch_issue = OutPort(DualMicroOp)  # for adding microops to branch issue queue

        s.uop1_dispatch = SingleDispatch()
        s.uop1_dispatch.in_ //= s.in_.uop1
        s.to_rob.uop1 //= s.uop1_dispatch.to_rob
        s.to_int_issue.uop1 //= s.uop1_dispatch.to_int_issue
        s.to_mem_issue.uop1 //= s.uop1_dispatch.to_mem_issue
        s.to_branch_issue.uop1 //= s.uop1_dispatch.to_branch_issue

        s.uop2_dispatch = SingleDispatch()
        s.uop2_dispatch.in_ //= s.in_.uop2
        s.to_rob.uop2 //= s.uop2_dispatch.to_rob
        s.to_int_issue.uop2 //= s.uop2_dispatch.to_int_issue
        s.to_mem_issue.uop2 //= s.uop2_dispatch.to_mem_issue
        s.to_branch_issue.uop2 //= s.uop2_dispatch.to_branch_issue

        @update
        def update_rob_idx():
            s.uop1_dispatch.rob_idx @= s.rob_idx
            s.uop2_dispatch.rob_idx @= s.rob_idx + 1

            s.uop1_dispatch.mem_q_idx @= 0
            s.uop2_dispatch.mem_q_idx @= 0
            # uop1 and uop2 in buffer
            if (s.in_.uop1.issue_unit == MEM_ISSUE_UNIT) & (
                s.in_.uop2.issue_unit == MEM_ISSUE_UNIT
            ):
                s.uop1_dispatch.mem_q_idx @= s.mem_q_tail - 2
                s.uop2_dispatch.mem_q_idx @= s.mem_q_tail - 1
            # uop1 is in ls buffer
            elif s.in_.uop1.issue_unit == MEM_ISSUE_UNIT:
                s.uop1_dispatch.mem_q_idx @= s.mem_q_tail - 1
            # uop2 is in ls buffer
            elif s.in_.uop2.issue_unit == MEM_ISSUE_UNIT:
                s.uop2_dispatch.mem_q_idx @= s.mem_q_tail - 1

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
        s.rob_idx = InPort(clog2(ROB_SIZE))  # for updating uops with ROB index
        s.mem_q_idx = InPort(clog2(MEM_Q_SIZE))
        s.to_rob = OutPort(MicroOp)  # for adding microops to ROB

        s.to_int_issue = OutPort(MicroOp)  # for adding microops to int issue queue
        s.to_mem_issue = OutPort(MicroOp)  # for adding microops to mem issue queue
        s.to_branch_issue = OutPort(MicroOp)  # for adding microops to branch issue queue

        @update
        def conditional_dispatch():
            s.to_rob @= s.in_

        @update
        def issue():
            if s.in_.issue_unit == INT_ISSUE_UNIT:
                s.to_int_issue @= s.in_
                s.to_int_issue.rob_idx @= s.rob_idx
                s.to_int_issue.mem_q_idx @= 0
            else:
                s.to_int_issue @= NO_OP
            if s.in_.issue_unit == MEM_ISSUE_UNIT:
                s.to_mem_issue @= s.in_
                s.to_mem_issue.rob_idx @= s.rob_idx
                s.to_mem_issue.mem_q_idx @= s.mem_q_idx
            else:
                s.to_mem_issue @= NO_OP
            if s.in_.funct_unit == BRANCH_FUNCT_UNIT:
                s.to_branch_issue @= s.in_
                s.to_branch_issue.rob_idx @= s.rob_idx
                s.to_branch_issue.mem_q_idx @= 0
            else:
                s.to_branch_issue @= NO_OP
