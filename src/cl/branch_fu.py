# Branch calculation functional unit.
# Responsible for redirecting the pipeline when a branch is mispredicted.

from pymtl3 import Component, InPort, OutPort, update, bitstruct, mk_bits, clog2
from pymtl3.stdlib.ifcs import RecvIfcRTL, SendIfcRTL
from src.common.interfaces import BranchUpdate, MicroOp
from src.common.consts import (
    BRANCH_FUNCT_UNIT,
    BFU_BEQ,
    BFU_BNE,
    BFU_BLT,
    BFU_BGE,
    BFU_BLTU,
    BFU_BGEU,
)

# TODO: make a parent class for all functional units
class BranchFU(Component):
    def construct(s):
        s.rs1_din = InPort(32)
        s.rs2_din = InPort(32)
        s.uop = InPort(MicroOp)

        # TODO: redirect address for now, will contain more metedata later
        s.br_update = SendIfcRTL(BranchUpdate)

        # TODO: Code for linking registers for JAL and JALR

        @update
        def updt():
            # for signed logic
            rs1_neg = s.rs1_din[32 - 1]
            rs2_neg = s.rs2_din[32 - 1]
            sign_diff = rs1_neg ^ rs2_neg
            s.br_update.en @= s.uop.funct_unit == BRANCH_FUNCT_UNIT
            s.br_update.msg.tag @= s.uop.br_tag

            # if branch taken...
            if (
                ((s.uop.funct_op == BFU_BEQ) & (s.rs1_din == s.rs2_din))
                | ((s.uop.funct_op == BFU_BNE) & (s.rs1_din != s.rs2_din))
                | (
                    (s.uop.funct_op == BFU_BLT)
                    & ((sign_diff & rs1_neg) | (~sign_diff & (s.rs1_din < s.rs2_din)))
                )
                | (
                    (s.uop.funct_op == BFU_BGE)
                    & ((sign_diff & rs2_neg) | (~sign_diff & (s.rs1_din >= s.rs2_din)))
                )
                | ((s.uop.funct_op == BFU_BLTU) & (s.rs1_din < s.rs2_din))
                | ((s.uop.funct_op == BFU_BGEU) & (s.rs1_din >= s.rs2_din))
            ):

                # mispredict if branch is predicted not taken but taken
                s.br_update.msg.mispredict @= ~s.uop.branch_taken
                s.br_update.msg.target @= s.uop.pc + s.uop.imm

            # if branch not taken...
            else:
                # mispredict if branch is predicted taken but not taken
                s.br_update.msg.mispredict @= s.uop.branch_taken
                s.br_update.msg.target @= s.uop.pc + 8

    def line_trace(s):
        en = s.br_update.en
        return (
            f"rs1: {s.rs1_din} rs2: {s.rs2_din} "
            f"mispredict: {s.br_update.msg.mispredict if en else 'none'} "
            f"target: {s.br_update.msg.target if en else 'none'} "
            f"tag: {s.br_update.msg.tag if en else 'none'}"
        )
