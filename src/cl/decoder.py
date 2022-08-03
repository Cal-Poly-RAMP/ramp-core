from pymtl3 import *
from pymtl3.stdlib import stream

from src.cl.fetch_stage import FetchPacket
from src.cl.register_rename import (
    RegisterRename,
    LogicalRegs,
    PhysicalRegs,
    PRegBusy,
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
    # For decoding fetch packet into two micro-ops
    def construct(s):
        # Interface (fetch packet in, dual uops out)
        s.fetch_packet = InPort(FetchPacket)
        s.inst1 = Wire(32)
        s.inst2 = Wire(32)
        s.inst1 //= s.fetch_packet.inst1
        s.inst2 //= s.fetch_packet.inst2

        s.dual_uop = OutPort(DualMicroOp)

        s.d1 = SingleInstDecode()
        # instruction in
        s.d1.inst //= s.inst1
        # uop out...
        s.d1.uop //= s.dual_uop.uop1

        s.d2 = SingleInstDecode()
        # instruction in
        s.d2.inst //= s.inst2
        # uop out...
        s.d2.uop //= s.dual_uop.uop2

        s.register_rename = RegisterRename()
        # logical registers in...
        s.register_rename.inst1_lregs.lrd //= s.d1.uop.lrd
        s.register_rename.inst1_lregs.lrs1 //= s.d1.uop.lrs1
        s.register_rename.inst1_lregs.lrs2 //= s.d1.uop.lrs2
        s.register_rename.inst2_lregs.lrd //= s.d2.uop.lrd
        s.register_rename.inst2_lregs.lrs1 //= s.d2.uop.lrs1
        s.register_rename.inst2_lregs.lrs2 //= s.d2.uop.lrs2
        # physical registers out...
        s.register_rename.inst1_pregs.prd //= s.d1.pregs.prd
        s.register_rename.inst1_pregs.prs1 //= s.d1.pregs.prs1
        s.register_rename.inst1_pregs.prs2 //= s.d1.pregs.prs2
        s.register_rename.inst1_pregs.stale //= s.d1.pregs.stale
        s.register_rename.inst2_pregs.prd //= s.d2.pregs.prd
        s.register_rename.inst2_pregs.prs1 //= s.d2.pregs.prs1
        s.register_rename.inst2_pregs.prs2 //= s.d2.pregs.prs2
        s.register_rename.inst2_pregs.stale //= s.d2.pregs.stale

        # pregs busy status out...
        s.register_rename.inst1_pregs_busy //= s.d1.pregs_busy
        s.register_rename.inst2_pregs_busy //= s.d2.pregs_busy

        # @update
        # def decode_comb_i1():
        #     pass

        # @update_ff
        # def decode_sync():
        #     pass

    def line_trace(s):
        return (
            f"\tfetch packet:\t{s.fetch_packet}"
            + f"\n\tuop1:\t{s.dual_uop.uop1} \n\tuop2:\t{s.dual_uop.uop2}"
        )


class SingleInstDecode(Component):
    # For decoding a single instruction into one micro-op, with info from register renaming
    def construct(s):
        s.inst = InPort(32)  # instruction from fetch packet
        s.pregs = InPort(PhysicalRegs)  # physical registers from register rename
        s.pregs_busy = InPort(PRegBusy)  # busy table from register rename
        s.uop = OutPort(MicroOp)

        @update
        def decode_comb():
            # For determining type
            opcode = s.inst[0:7]

            Rtype = opcode == 0b0110011
            Itype = (
                (opcode == 0b0010011) | (opcode == 0b0000011) | (opcode == 0b1100111)
            )
            Stype = opcode == 0b0100011
            Btype = opcode == 0b1100011
            Utype = (opcode == 0b0110111) | (opcode == 0b0010111)
            Jtype = opcode == 0b1101111
            Csrtype = opcode == 0b1110011

            # uop (hardcoded values)
            s.uop.inst @= s.inst
            s.uop.pc @= 0  # TODO

            s.uop.lrd @= s.inst[RD_BEG:RD_END]
            s.uop.lrs1 @= s.inst[RS1_BEG:RS1_END]
            s.uop.lrs2 @= s.inst[RS2_BEG:RS2_END]

            s.uop.prd @= s.pregs.prd
            s.uop.prs1 @= s.pregs.prs1
            s.uop.prs2 @= s.pregs.prs2
            s.uop.stale @= s.pregs.stale

            # s.uop.prd_busy @= s.register_rename.busy_table[
            #     s.uop.prd
            # ]  # should always be true, do i need this?
            s.uop.prs1_busy @= s.pregs_busy.prs1
            s.uop.prs2_busy @= s.pregs_busy.prs2

            # immediates
            if Rtype:
                s.uop.imm @= 0
            elif Itype:
                s.uop.imm @= sext(s.inst[20:32], 32)
                s.uop.lrs2 @= 0
            elif Stype:
                s.uop.imm @= sext(concat(s.inst[25:32], s.inst[7:12]), 32)
                s.uop.lrd @= 0
            elif Btype:
                s.uop.imm @= sext(
                    concat(
                        s.inst[31], s.inst[7], s.inst[25:31], s.inst[8:12], Bits1(0)
                    ),
                    32,
                )
                s.uop.lrd @= 0
            elif Utype:
                s.uop.imm @= concat(s.inst[12:32], Bits12(0))
                s.uop.lrs1 @= 0
                s.uop.lrs2 @= 0
            elif Jtype:
                s.uop.imm @= sext(
                    concat(
                        s.inst[31],
                        s.inst[12:20],
                        s.inst[20],
                        s.inst[25:31],
                        s.inst[21:25],
                        Bits1(0),
                    ),
                    32,
                )
                s.uop.lrs1 @= 0
                s.uop.lrs2 @= 0
            elif Csrtype:
                s.uop.imm @= 0
                s.uop.lrs2 @= 0


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

    # prd_busy: Bits1  # physical destination register busy
    prs1_busy: Bits1  # physical source register 1 busy
    prs2_busy: Bits1  # physical source register 2 busy

    imm: Bits32  # immediate TODO: encode to be smaller, and use sign extension TODO: 64 bit?

    issue_unit: Bits2  # issue unit
    fu_unit: Bits2  # functional unit
    fu_op: Bits2  # functional unit operation

    # TODO: branch prediction fields
    def __str__(s):
        return "uop_code: {} inst: {} pc: {} imm: {} issue_unit: {} fu_unit: {} fu_op: {} \n\t\tlrd: x{:02d} lrs1: x{:02d} lrs2: x{:02d} prd: x{:02d} prs1: x{:02d} prs2: x{:02d} stale: x{:02d} prs1_busy: {} prs2_busy: {}".format(
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
            # s.prd_busy,
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