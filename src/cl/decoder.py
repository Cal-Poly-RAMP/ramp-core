from pymtl3 import *
from pymtl3.stdlib import stream

from src.cl.fetch_stage import FetchPacket
from src.cl.register_rename import (
    RegisterRename,
    LogicalRegs,
    PhysicalRegs,
    NUM_PHYS_REGS,
    NUM_ISA_REGS,
    PHYS_REG_BITWIDTH,
    ISA_REG_BITWIDTH,
)

# Decoding consts
RD_BEG = 7
RD_END = 12
RS1_BEG = 15
RS1_END = 20
RS2_BEG = 20
RS2_END = 25


class Decode(Component):
    def construct(s):
        # Interface (fetch packet)
        s.fetch_packet = InPort(FetchPacket)
        s.inst1 = Wire(32)
        s.inst2 = Wire(32)
        s.inst1 //= s.fetch_packet.inst1
        s.inst2 //= s.fetch_packet.inst2

        s.dual_uop = OutPort(DualMicroOp)
        s.uop1 = Wire(MicroOp)
        s.uop2 = Wire(MicroOp)
        s.dual_uop.uop1 //= s.uop1
        s.dual_uop.uop2 //= s.uop2

        # s.uop1 = s.dual_uop.uop1
        # s.uop2 = s.dual_uop.uop2
        # s.inst1 = s.fetch_packet.inst1
        # s.inst2 = s.fetch_packet.inst2

        s.register_rename = RegisterRename()
        s.register_rename.inst1_lregs.lrd //= s.uop1.lrd
        s.register_rename.inst1_lregs.lrs1 //= s.uop1.lrs1
        s.register_rename.inst1_lregs.lrs2 //= s.uop1.lrs2
        s.register_rename.inst2_lregs.lrd //= s.uop2.lrd
        s.register_rename.inst2_lregs.lrs1 //= s.uop2.lrs1
        s.register_rename.inst2_lregs.lrs2 //= s.uop2.lrs2

        @update
        def decode_comb_i1():
            # UOP1 -------------------------------------------------------------
            # For determining type
            i1_opcode = s.inst1[0:7]

            i1_Rtype = i1_opcode == 0b0110011
            i1_Itype = (
                (i1_opcode == 0b0010011)
                or (i1_opcode == 0b0000011)
                or (i1_opcode == 0b1100111)
            )
            i1_Stype = i1_opcode == 0b0100011
            i1_Btype = i1_opcode == 0b1100011
            i1_Utype = (i1_opcode == 0b0110111) or (i1_opcode == 0b0010111)
            i1_Jtype = i1_opcode == 0b1101111
            i1_Csrtype = i1_opcode == 0b1110011

            # UOP1 (hardcoded values)
            s.uop1.inst @= s.inst1
            s.uop1.pc @= 0  # TODO

            s.uop1.lrd @= s.inst1[RD_BEG:RD_END]
            s.uop1.lrs1 @= s.inst1[RS1_BEG:RS1_END]
            s.uop1.lrs2 @= s.inst1[RS2_BEG:RS2_END]

            s.uop1.prd @= s.register_rename.inst1_pregs.prd
            s.uop1.prs1 @= s.register_rename.inst1_pregs.prs1
            s.uop1.prs2 @= s.register_rename.inst1_pregs.prs2
            s.uop1.stale @= s.register_rename.inst1_pregs.stale

            s.uop1.prd_busy @= s.register_rename.busy_table[
                s.uop1.prd
            ]  # should always be true, do i need this?
            s.uop1.prs1_busy @= s.register_rename.busy_table[s.uop1.prs1]
            s.uop1.prs2_busy @= s.register_rename.busy_table[s.uop1.prs2]

            # immediates
            if i1_Rtype:
                s.uop1.imm @= 0
            elif i1_Itype:
                s.uop1.imm @= sext(s.inst1[20:32], 32)
            elif i1_Stype:
                s.uop1.imm @= sext(concat(s.inst1[25:32], s.inst1[7:12]), 32)
            elif i1_Btype:
                s.uop1.imm @= sext(
                    concat(s.inst1[31], s.inst1[7], s.inst1[25:31], s.inst1[8:12]), 32
                )
            elif i1_Utype:
                s.uop1.imm @= concat(s.inst1[12:32], Bits12(0))
            elif i1_Jtype:
                s.uop1.imm @= sext(
                    concat(
                        s.inst1[31],
                        s.inst1[12:20],
                        s.inst1[20],
                        s.inst1[25:31],
                        s.inst1[21:25],
                        Bits1(0),
                    ),
                    32,
                )
            elif i1_Csrtype:
                s.uop1.imm @= 0

            # UOP2 -------------------------------------------------------------
            # For determining type
            i2_opcode = s.inst1[0:7]

            i2_Rtype = i2_opcode == 0b0110011
            i2_Itype = (
                (i2_opcode == 0b0010011)
                or (i2_opcode == 0b0000011)
                or (i2_opcode == 0b1100111)
            )
            i2_Stype = i2_opcode == 0b0100011
            i2_Btype = i2_opcode == 0b1100011
            i2_Utype = (i2_opcode == 0b0110111) or (i2_opcode == 0b0010111)
            i2_Jtype = i2_opcode == 0b1101111
            i2_Csrtype = i2_opcode == 0b1110011

            # UOP2 (hardcoded values)
            s.uop2.inst @= s.inst2
            s.uop2.pc @= 0  # TODO

            s.uop2.lrd @= s.inst2[RD_BEG:RD_END]
            s.uop2.lrs1 @= s.inst2[RS1_BEG:RS1_END]
            s.uop2.lrs2 @= s.inst2[RS2_BEG:RS2_END]

            s.uop2.prd @= s.register_rename.inst2_pregs.prd
            s.uop2.prs1 @= s.register_rename.inst2_pregs.prs1
            s.uop2.prs2 @= s.register_rename.inst2_pregs.prs2
            s.uop2.stale @= s.register_rename.inst2_pregs.stale

            s.uop2.prd_busy @= s.register_rename.busy_table[
                s.uop2.prd
            ]  # should always be true, do i need this?
            s.uop2.prs1_busy @= s.register_rename.busy_table[s.uop2.prs1]
            s.uop2.prs2_busy @= s.register_rename.busy_table[s.uop2.prs2]

            # immediates
            if i2_Rtype:
                s.uop2.imm @= 0
            elif i2_Itype:
                s.uop2.imm @= sext(s.inst2[20:32], 32)
            elif i2_Stype:
                s.uop2.imm @= sext(concat(s.inst2[25:32], s.inst2[7:12]), 32)
            elif i2_Btype:
                s.uop2.imm @= sext(
                    concat(s.inst2[31], s.inst2[7], s.inst2[25:31], s.inst2[8:12]), 32
                )
            elif i2_Utype:
                s.uop2.imm @= concat(s.inst2[12:32], Bits12(0))
            elif i2_Jtype:
                s.uop2.imm @= sext(
                    concat(
                        s.inst2[31],
                        s.inst2[12:20],
                        s.inst2[20],
                        s.inst2[25:31],
                        s.inst2[21:25],
                        Bits1(0),
                    ),
                    32,
                )
            elif i2_Csrtype:
                s.uop2.imm @= 0

        @update_ff
        def decode_sync():
            pass

    def line_trace(s):
        return "\tfetch packet:\t{}".format(
            s.fetch_packet
        ) + "\n\tuop1:\t{} \n\tuop2:\t{}".format(s.uop1, s.uop2)


@bitstruct
class MicroOp:
    uop_code: Bits4  # micro-op type
    inst: Bits32  # instruction
    pc: Bits32  # program counter

    lrd: mk_bits(ISA_REG_BITWIDTH)  # logical destination register
    lrs1: mk_bits(ISA_REG_BITWIDTH)  # logical source register 1
    lrs2: mk_bits(ISA_REG_BITWIDTH)  # logical source register 2

    prd: mk_bits(PHYS_REG_BITWIDTH)  # physical dest register
    prs1: mk_bits(PHYS_REG_BITWIDTH)  # physical source register 1
    prs2: mk_bits(PHYS_REG_BITWIDTH)  # physical source register 2
    stale: mk_bits(PHYS_REG_BITWIDTH)  # stale physical register

    prd_busy: Bits1  # physical destination register busy
    prs1_busy: Bits1  # physical source register 1 busy
    prs2_busy: Bits1  # physical source register 2 busy

    imm: Bits32  # immediate TODO: encode to be smaller, and use sign extension TODO: 64 bit?

    issue_unit: Bits2  # issue unit
    fu_unit: Bits2  # functional unit
    fu_op: Bits2  # functional unit operation

    # TODO: branch prediction fields
    def __str__(s):
        return "uop_code: {} inst: {} pc: {} imm: {} issue_unit: {} fu_unit: {} fu_op: {} \n\t\tlrd: x{:02d} lrs1: x{:02d} lrs2: x{:02d} prd: x{:02d} prs1: x{:02d} prs2: x{:02d} stale: x{:02d} prd_busy: {} prs1_busy: {} prs2_busy: {}".format(
            s.uop_code,
            s.inst,
            s.pc,
            s.imm,
            s.issue_unit,
            s.fu_unit,
            s.fu_op,
            s.lrd.uint(),
            s.lrs1.uint(),
            s.lrs2.uint(),
            s.prd.uint(),
            s.prs1.uint(),
            s.prs2.uint(),
            s.stale.uint(),
            s.prd_busy,
            s.prs1_busy,
            s.prs2_busy,
        )


@bitstruct
class DualMicroOp:
    uop1: MicroOp
    uop2: MicroOp


# Used for deriving data from instructions
@bitstruct
class GenericInstPattern:
    funct7: Bits7
    rs2: Bits5
    rs1: Bits5
    funct3: Bits3
    rd: Bits5
    opcode: Bits7


# @bitstruct
# class RTypeIntrPattern:
