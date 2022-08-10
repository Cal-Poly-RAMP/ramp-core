# The ReOrder Buffer
# TODO: there can be much optimization to make smaller.
# TODO: NOT SYNTHESIZEABLE
# We are going to store full microops in the ROB, but for synthesis, only certain
# fields are needed.
from pymtl3 import (
    Bits,
    Bits1,
    Component,
    InPort,
    OutPort,
    bitstruct,
    mk_bits,
    update,
    update_ff,
    Wire,
    sext,
)
from src.cl.decoder import NO_OP, ROB_ADDR_WIDTH, ROB_SIZE, DualMicroOp, MicroOp
from src.cl.fetch_stage import PC_WIDTH
from src.cl.register_rename import ISA_REG_BITWIDTH, PHYS_REG_BITWIDTH

## TODO NOW: make it so that `valid` is only a flag, not set by the ROB. `Busy` the only one set by ROB
class ReorderBuffer(Component):
    def construct(s):
        # Interface (dual uops in, dual uops out)
        s.write_in = InPort(DualMicroOp)  # getting microps from dispatch
        s.commit_out = OutPort(ROBEntry)  # for committing microops to mem
        s.uop1_entry = Wire(ROBEntryUop)
        s.uop2_entry = Wire(ROBEntryUop)
        s.commit_out.uop1_entry //= s.uop1_entry
        s.commit_out.uop2_entry //= s.uop2_entry
        s.op_complete = InPort(ExecToROB)  # for updating completed microops in ROB

        # Defining the instruction bank for storing inflight instructions
        # 1 smaller, because the uops are stored in sets of two in the ROB, but
        # indexed individually.
        s.internal_rob_head = Wire(ROB_ADDR_WIDTH - 1)
        s.internal_rob_tail = Wire(ROB_ADDR_WIDTH - 1)
        # for updating microops with ROB index
        s.rob_tail = OutPort(ROB_ADDR_WIDTH)

        # a circular buffer of entries
        s.instr_bank = [ROBEntry() for _ in range(ROB_SIZE // 2)]
        s.bank_full = OutPort(1)
        s.bank_empty = OutPort(1)

        @update
        def comb_():
            # indexed so that uop1 is at odd indices and uop2 is at even indices
            s.rob_tail @= sext(s.internal_rob_tail, ROB_ADDR_WIDTH) << 1

            # bank full if head == tail and value is busy
            s.bank_full @= (
                (s.internal_rob_head == s.internal_rob_tail)
                & s.instr_bank[s.internal_rob_tail].uop1_entry.busy
                & s.instr_bank[s.internal_rob_tail].uop2_entry.busy
            )

            # bank empty if head == tail and value is invalid(TODO: ?)
            s.bank_empty @= (s.internal_rob_head == s.internal_rob_tail) & ~(
                s.instr_bank[s.internal_rob_tail].uop1_entry.busy
                | s.instr_bank[s.internal_rob_tail].uop2_entry.busy
            )

        @update_ff
        def sync_():
            # SYNCHRONOUS RESET
            if s.reset:
                s.internal_rob_head <<= 0
                s.internal_rob_tail <<= 0
                for i in range(ROB_SIZE >> 1):
                    s.instr_bank[i].uop1_entry.valid <<= 0
                    s.instr_bank[i].uop2_entry.valid <<= 0
                    s.instr_bank[i].uop1_entry.busy <<= 0
                    s.instr_bank[i].uop2_entry.busy <<= 0
                return

            # WRITING TO ROB
            # if either of the uops is valid, and there is room in the buffer,
            # write both to the ROB
            if s.write_in.uop1.valid | s.write_in.uop2.valid:
                # if the circular buffer is not full
                if ~s.bank_full:
                    s.instr_bank[s.internal_rob_tail] = ROBEntry(
                        pc=s.write_in.uop1.pc,
                        uop1_entry=ROBEntryUop(
                            valid=s.write_in.uop1.valid,
                            busy=s.write_in.uop1.valid,  # busy if valid
                            type=s.write_in.uop1.type,
                            lrd=s.write_in.uop1.lrd,
                            stale=s.write_in.uop1.stale,
                        ),
                        uop2_entry=ROBEntryUop(
                            valid=s.write_in.uop2.valid,
                            busy=s.write_in.uop1.valid,  # busy if valid
                            type=s.write_in.uop2.type,
                            lrd=s.write_in.uop2.lrd,
                            stale=s.write_in.uop2.stale,
                        ),
                    )
                    s.internal_rob_tail <<= s.internal_rob_tail + 1  # wrap around
                else:
                    raise OverflowError("ROB is full, and tried to write")

            # UPDATING COMPLETED UOPS
            # even though actual instruction bank is 2 wide,
            # uop1 and uop2 are indexed seperately (even and odd respectively)
            # rob indices must be calculated from these indices in the uop
            if s.op_complete.int_rob_complete:
                if s.op_complete.int_rob_idx % 2 == 0:
                    # even index, uop1 is completed
                    s.instr_bank[
                        s.op_complete.int_rob_idx >> 1
                    ].uop1_entry.busy = Bits1(0)
                else:
                    # odd index, uop2 is completed
                    s.instr_bank[
                        s.op_complete.int_rob_idx >> 1
                    ].uop2_entry.busy = Bits1(0)
            if s.op_complete.mem_rob_complete:
                if s.op_complete.mem_rob_idx % 2 == 0:
                    # even index, uop1 is completed
                    s.instr_bank[
                        s.op_complete.mem_rob_idx >> 1
                    ].uop1_entry.busy = Bits1(0)
                else:
                    # odd index, uop2 is completed
                    s.instr_bank[
                        s.op_complete.mem_rob_idx >> 1
                    ].uop2_entry.busy = Bits1(0)

            # COMMITTING
            # committed store instructions write to memory
            # committed arithmetic instructions deallocate stale reg

            # if the ROB's head entry uop1 is valid and not busy, commit it
            if (
                s.instr_bank[s.internal_rob_head].uop1_entry.valid
                & ~s.instr_bank[s.internal_rob_head].uop1_entry.busy
            ):
                s.uop1_entry <<= s.instr_bank[s.internal_rob_head].uop1_entry
                s.instr_bank[s.internal_rob_head].uop1_entry.valid = Bits1(0)
            # otherwise do not commit it
            else:
                s.uop1_entry <<= ROBEntryUop(0, 0, 0)
            # if the ROB's head entry uop2 is valid and not busy, commit it
            if (
                s.instr_bank[s.internal_rob_head].uop2_entry.valid
                & ~s.instr_bank[s.internal_rob_head].uop2_entry.busy
            ):
                s.uop2_entry <<= s.instr_bank[s.internal_rob_head].uop2_entry
                s.instr_bank[s.internal_rob_head].uop2_entry.valid = Bits1(0)
            # otherwise do not commit it
            else:
                s.uop2_entry <<= ROBEntryUop(0, 0, 0)

            # if the ROB's head entry is not busy (committed), deallocate it
            if (
                ~s.instr_bank[s.internal_rob_head].uop1_entry.busy
                & ~s.instr_bank[s.internal_rob_head].uop2_entry.busy
            ):
                # if the circular buffer is not empty
                if ~s.bank_empty:
                    s.internal_rob_head <<= s.internal_rob_head + 1
                else:
                    raise Exception("ROB is empty, and tried to deallocate")

    def line_trace(s):
        return (
            f"\tWrite In: {s.write_in.uop1}\n\t\t{s.write_in.uop2} \n\tOp Complete In: {s.op_complete} \n\tCommit Out: {s.commit_out}"
            f"\n\tExternal ROB head: {s.internal_rob_head * 2} External ROB tail: {s.internal_rob_tail * 2}"
            f"\n\tBank Full: {s.bank_full} Bank Empty: {s.bank_empty}"
            f"\n\tInstr Bank : {[str(x) if x.to_bits() else 0 for x in s.instr_bank]}\n"
        )


@bitstruct
class ROBEntryUop:
    valid: mk_bits(1)
    busy: mk_bits(1)
    type: mk_bits(3)
    lrd: mk_bits(ISA_REG_BITWIDTH)
    stale: mk_bits(PHYS_REG_BITWIDTH)


@bitstruct
class ROBEntry:
    pc: mk_bits(PC_WIDTH)
    uop1_entry: ROBEntryUop
    uop2_entry: ROBEntryUop


# comes from execution units, to set ROB entries as complete (not busy)
@bitstruct
class ExecToROB:
    # index of the operation just completed by int alu, and whether it is valid
    int_rob_idx: mk_bits(ROB_ADDR_WIDTH)
    int_rob_complete: mk_bits(1)
    # index of the operation just completed by mem unit, and whether it is valid
    mem_rob_idx: mk_bits(ROB_ADDR_WIDTH)
    mem_rob_complete: mk_bits(1)
