# The ReOrder Buffer
# TODO: REDO EVERYTHING USING NEW QUEUES
# We are going to store full microops in the ROB, but for synthesis, only certain
# fields are needed.
from pymtl3 import (
    Component,
    InPort,
    OutPort,
    Wire,
    bitstruct,
    mk_bits,
    sext,
    update,
    update_ff,
    clog2,
    Bits,
    zext,
    trunc
)
from pymtl3.stdlib.ifcs import RecvIfcRTL, SendIfcRTL

from src.common.consts import (
    MEM_Q_SIZE,
    NUM_BRANCHES,
    ROB_SIZE,
    ROB_SIZE,
    NUM_ISA_REGS,
    NUM_PHYS_REGS,
)
from src.common.interfaces import DualMicroOp, BranchUpdate

## TODO NOW: make it so that `valid` is only a flag, not set by the ROB. `Busy` the only one set by ROB
class ReorderBuffer(Component):
    def construct(s):
        # Interface (dual uops in, dual uops out)
        s.write_in = InPort(DualMicroOp)  # getting microps from dispatch
        s.commit_out = OutPort(ROBEntry)  # for committing microops to mem
        s.uop1_entry = Wire(ROBEntryUop)
        s.uop1_entry_next = Wire(ROBEntryUop)
        s.uop2_entry = Wire(ROBEntryUop)
        s.uop2_entry_next = Wire(ROBEntryUop)
        s.commit_out.uop1_entry //= s.uop1_entry
        s.commit_out.uop2_entry //= s.uop2_entry
        s.op_complete = InPort(ExecToROB)  # for updating completed microops in ROB

        # Defining the instruction bank for storing inflight instructions
        # 1 smaller, because the uops are stored in sets of two in the ROB, but
        # indexed individually.
        s.internal_rob_head = Wire(clog2(ROB_SIZE) - 1)
        s.internal_rob_head_next = Wire(clog2(ROB_SIZE) - 1)
        s.internal_rob_tail = Wire(clog2(ROB_SIZE) - 1)
        s.internal_rob_tail_next = Wire(clog2(ROB_SIZE) - 1)
        # for updating microops with ROB index
        s.rob_tail = OutPort(clog2(ROB_SIZE))

        # a circular buffer of entries
        s.instr_bank = [Wire(ROBEntry) for _ in range(ROB_SIZE // 2)]
        s.instr_bank_next = [Wire(ROBEntry) for _ in range(ROB_SIZE // 2)]
        s.bank_full = OutPort(1)
        s.bank_empty = OutPort(1)

        # for branch updates (mispredicted or predicted correctly)
        s.br_update = RecvIfcRTL(BranchUpdate)
        s.br_update.rdy //= Bits(1, 1)

        rob_addr_nbits = clog2(ROB_SIZE)
        instr_bank_addr_nbits = clog2(ROB_SIZE) - 1
        empty_rob_entry = ROBEntryUop(0)

        one = Bits(1, 1)

        @update
        def comb_():
            # indexed so that uop1 is at odd indices and uop2 is at even indices
            s.rob_tail @= zext(s.internal_rob_tail, rob_addr_nbits) << 1

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

            # defaults
            s.internal_rob_head_next @= s.internal_rob_head
            s.internal_rob_tail_next @= s.internal_rob_tail
            s.uop1_entry_next @= empty_rob_entry
            s.uop1_entry_next @= empty_rob_entry
            for i in range(ROB_SIZE >> 1):
                s.instr_bank_next[i] @= s.instr_bank[i]

            # WRITING TO ROB
            # if either of the uops is valid, and there is room in the buffer,
            # write both to the ROB
            if s.write_in.uop1.valid | s.write_in.uop2.valid:
                # if the circular buffer is not full
                # TODO: assert for CL
                # assert ~s.bank_full, "ROB is full and tried to write"
                s.instr_bank_next[s.internal_rob_tail] @= ROBEntry(
                    s.write_in.uop1.pc,                 # PC
                    ROBEntryUop(                        # uop1
                        s.write_in.uop1.valid,          # valid
                        s.write_in.uop1.valid,          # busy
                        s.write_in.uop1.optype,         # optype
                        s.write_in.uop1.prd,            # prd
                        s.write_in.uop1.stale,          # stale
                        0,                              # data
                        0,                              # mem_q_idx
                        0,                              # store_addr
                        0,                              # br_target
                        0,                              # br_tag
                        0,                              # br_mispredict
                        s.write_in.uop1.br_mask,        # br_mask
                    ),
                    ROBEntryUop(                        # uop2
                        s.write_in.uop2.valid,          # valid
                        s.write_in.uop2.valid,          # busy
                        s.write_in.uop2.optype,         # optype
                        s.write_in.uop2.prd,            # prd
                        s.write_in.uop2.stale,          # stale
                        0,                              # data
                        0,                              # mem_q_idx
                        0,                              # store_addr
                        0,                              # br_target
                        0,                              # br_tag
                        0,                              # br_mispredict
                        s.write_in.uop2.br_mask,        # br_mask
                    ),
                )
                s.internal_rob_tail_next @= s.internal_rob_tail + 1  # wrap around

            # UPDATING COMPLETED UOPS
            # even though actual instruction bank is 2 wide,
            # uop1 and uop2 are indexed seperately (even and odd respectively)
            # rob indices must be calculated from these indices in the uop

            # INTEGER UPDATES
            internal_int_rob_addr = trunc(s.op_complete.int_rob_idx >> 1, instr_bank_addr_nbits)
            if s.op_complete.int_rob_complete:
                if s.op_complete.int_rob_idx % 2 == 0:
                    # even index, uop1 is completed
                    s.instr_bank_next[internal_int_rob_addr].uop1_entry.busy @= 0
                    s.instr_bank_next[
                        internal_int_rob_addr
                    ].uop1_entry.data @= s.op_complete.int_data
                else:
                    # odd index, uop2 is completed
                    s.instr_bank_next[internal_int_rob_addr].uop2_entry.busy @= 0
                    s.instr_bank_next[
                        internal_int_rob_addr
                    ].uop2_entry.data @= s.op_complete.int_data

            # LOAD UPDATES
            internal_load_rob_addr = trunc(s.op_complete.load_rob_idx >> 1, instr_bank_addr_nbits)
            if s.op_complete.load_rob_complete:
                if s.op_complete.load_rob_idx % 2 == 0:
                    # even index, uop1 is completed
                    s.instr_bank_next[internal_load_rob_addr].uop1_entry.busy @= 0
                    s.instr_bank_next[
                        internal_load_rob_addr
                    ].uop1_entry.data @= s.op_complete.load_data
                else:
                    # odd index, uop2 is completed
                    s.instr_bank_next[internal_load_rob_addr].uop2_entry.busy @= 0
                    s.instr_bank_next[
                        internal_load_rob_addr
                    ].uop2_entry.data @= s.op_complete.load_data

            # STORE UPDATES
            internal_store_rob_addr = trunc(s.op_complete.store_rob_idx >> 1, instr_bank_addr_nbits)
            if s.op_complete.store_rob_complete:
                if s.op_complete.store_rob_idx % 2 == 0:
                    # even index, uop1 is completed
                    s.instr_bank_next[internal_store_rob_addr].uop1_entry.busy @= 0
                    s.instr_bank_next[
                        internal_store_rob_addr
                    ].uop1_entry.data @= s.op_complete.store_data
                    s.instr_bank_next[
                        internal_store_rob_addr
                    ].uop1_entry.store_addr @= s.op_complete.store_addr
                    s.instr_bank_next[
                        internal_store_rob_addr
                    ].uop1_entry.mem_q_idx @= s.op_complete.store_mem_q_idx
                else:
                    # odd index, uop2 is completed
                    s.instr_bank_next[internal_store_rob_addr].uop2_entry.busy @= 0
                    s.instr_bank_next[
                        internal_store_rob_addr
                    ].uop2_entry.data @= s.op_complete.store_data
                    s.instr_bank_next[
                        internal_store_rob_addr
                    ].uop2_entry.store_addr @= s.op_complete.store_addr
                    s.instr_bank_next[
                        internal_store_rob_addr
                    ].uop2_entry.mem_q_idx @= s.op_complete.store_mem_q_idx

            # BRANCH UPDATES
            internal_br_rob_addr = trunc(s.op_complete.br_rob_idx >> 1, instr_bank_addr_nbits)
            if s.op_complete.br_rob_complete:
                if s.op_complete.br_rob_idx % 2 == 0:
                    # even index, uop1 is completed
                    s.instr_bank_next[internal_br_rob_addr].uop1_entry.busy @= 0
                    s.instr_bank_next[
                        internal_br_rob_addr
                    ].uop1_entry.br_target @= s.op_complete.br_target
                    s.instr_bank_next[
                        internal_br_rob_addr
                    ].uop1_entry.br_tag @= s.op_complete.br_tag
                    s.instr_bank_next[
                        internal_br_rob_addr
                    ].uop1_entry.br_mispredict @= s.op_complete.br_mispredict
                else:
                    # odd index, uop2 is completed
                    s.instr_bank_next[internal_br_rob_addr].uop2_entry.busy @= 0
                    s.instr_bank_next[
                        internal_br_rob_addr
                    ].uop2_entry.br_target @= s.op_complete.br_target
                    s.instr_bank_next[
                        internal_br_rob_addr
                    ].uop2_entry.br_tag @= s.op_complete.br_tag
                    s.instr_bank_next[
                        internal_br_rob_addr
                    ].uop2_entry.br_mispredict @= s.op_complete.br_mispredict

            # BRANCH PREDICTION UPDATES (updating tags with branch outcomes)
            tag_mask = zext(one, NUM_BRANCHES) << zext(s.br_update.msg.tag, NUM_BRANCHES)

            if s.br_update.en:
                for i in range(ROB_SIZE >> 1):
                    # if the branch was predicted correctly, update bitmask
                    if ~s.br_update.msg.mispredict:
                        s.instr_bank_next[i].uop1_entry.br_mask @= (
                            s.instr_bank[i].uop1_entry.br_mask & ~tag_mask
                        )
                        s.instr_bank_next[i].uop2_entry.br_mask @= (
                            s.instr_bank[i].uop2_entry.br_mask & ~tag_mask
                        )
                    # if the branch was predicted incorrectly robentry is dependent on branch
                    # invalidate robentry
                    else:
                        if s.instr_bank[i].uop1_entry.br_mask & tag_mask:
                            s.instr_bank_next[i].uop1_entry.valid @= 0
                            s.instr_bank_next[i].uop1_entry.busy @= 0
                        if s.instr_bank[i].uop2_entry.br_mask & tag_mask:
                            s.instr_bank_next[i].uop2_entry.valid @= 0
                            s.instr_bank_next[i].uop2_entry.busy @= 0

            # COMMITTING
            # committed store instructions write to memory
            # committed arithmetic instructions deallocate stale reg

            # if the ROB's head entry uop1 is valid, not busy, and not under speculation, commit
            if (
                s.instr_bank_next[s.internal_rob_head_next].uop1_entry.valid
                & ~s.instr_bank_next[s.internal_rob_head_next].uop1_entry.busy
                & (s.instr_bank_next[s.internal_rob_head_next].uop1_entry.br_mask == 0)
            ):
                s.uop1_entry_next @= s.instr_bank_next[
                    s.internal_rob_head_next
                ].uop1_entry
                s.instr_bank_next[s.internal_rob_head_next].uop1_entry.valid @= 0
            # otherwise do not commit it
            else:
                s.uop1_entry_next @= empty_rob_entry
            # if the ROB's head entry uop2 is valid and not busy, commit it
            if (
                s.instr_bank_next[s.internal_rob_head_next].uop2_entry.valid
                & ~s.instr_bank_next[s.internal_rob_head_next].uop2_entry.busy
                & (s.instr_bank_next[s.internal_rob_head_next].uop1_entry.br_mask == 0)
            ):
                s.uop2_entry_next @= s.instr_bank_next[
                    s.internal_rob_head_next
                ].uop2_entry
                s.instr_bank_next[s.internal_rob_head_next].uop2_entry.valid @= 0
            # otherwise do not commit it
            else:
                s.uop2_entry_next @= empty_rob_entry

            # if the ROB's head entry is not busy (committed), deallocate it
            if (
                ~s.instr_bank_next[s.internal_rob_head_next].uop1_entry.valid
                & ~s.instr_bank_next[s.internal_rob_head_next].uop2_entry.valid
            ):
                # if the circular buffer is not empty
                if ~s.bank_empty:
                    s.internal_rob_head_next @= s.internal_rob_head_next + 1
                # else:
                #     raise Exception("ROB is empty, and tried to deallocate")


            # ASYNCHRONOUS RESET
            if s.reset:
                s.internal_rob_head_next @= 0
                s.internal_rob_tail_next @= 0
                s.uop1_entry_next @= empty_rob_entry
                s.uop1_entry_next @= empty_rob_entry

                for i in range(ROB_SIZE >> 1):
                    s.instr_bank_next[i].uop1_entry.valid @= 0
                    s.instr_bank_next[i].uop2_entry.valid @= 0
                    s.instr_bank_next[i].uop1_entry.busy @= 0
                    s.instr_bank_next[i].uop2_entry.busy @= 0

        @update_ff
        def sync_():
            s.internal_rob_head <<= s.internal_rob_head_next
            s.internal_rob_tail <<= s.internal_rob_tail_next
            s.uop1_entry <<= s.uop1_entry_next
            s.uop2_entry <<= s.uop2_entry_next
            for i in range(ROB_SIZE >> 1):
                s.instr_bank[i] <<= s.instr_bank_next[i]

    def line_trace(s):
        return (
            f"\n\tWrite In: {s.write_in.uop1}\n\t\t{s.write_in.uop2} \n\tOp Complete In: {s.op_complete} \n\tCommit Out: {s.commit_out}"
            f"\n\tExternal ROB head: {s.internal_rob_head * 2} External ROB tail: {s.internal_rob_tail * 2}"
            f"\n\tBank Full: {s.bank_full} Bank Empty: {s.bank_empty}"
            f"\n\tInstr Bank : {[str(x) if (x.uop1_entry.valid | x.uop2_entry.valid) else '-' for x in s.instr_bank]}\n"
        )


@bitstruct
class ROBEntryUop:
    valid: mk_bits(1)
    busy: mk_bits(1)
    optype: mk_bits(3)
    prd: mk_bits(clog2(NUM_PHYS_REGS))
    stale: mk_bits(clog2(NUM_PHYS_REGS))
    data: mk_bits(32)
    # for store instructions
    mem_q_idx: mk_bits(clog2(MEM_Q_SIZE))
    store_addr: mk_bits(32)
    # for branch prediction
    br_target: mk_bits(32)
    br_tag: mk_bits(clog2(NUM_BRANCHES))
    br_mispredict: mk_bits(1)
    br_mask: mk_bits(NUM_BRANCHES)


@bitstruct
class ROBEntry:
    pc: mk_bits(32)
    uop1_entry: ROBEntryUop
    uop2_entry: ROBEntryUop

    # def __str__(s):
    #     return f"{s.pc}|{s.uop1_entry}|{s.uop2_entry}"


# TODO: replace with array of ROBEntryUOPs
@bitstruct
class ExecToROB:
    # index of the operation just completed by int alu, and whether it is valid
    int_rob_idx: mk_bits(clog2(ROB_SIZE))
    int_rob_complete: mk_bits(1)
    int_data: mk_bits(32)
    # index of the load operation just completed by mem unit, and whether it is valid
    load_rob_idx: mk_bits(clog2(ROB_SIZE))
    load_rob_complete: mk_bits(1)
    load_data: mk_bits(32)
    # index of the store operation just completed by mem unit, and whether it is valid
    store_rob_idx: mk_bits(clog2(ROB_SIZE))
    store_mem_q_idx: mk_bits(clog2(MEM_Q_SIZE))
    store_rob_complete: mk_bits(1)
    store_addr: mk_bits(32)
    store_data: mk_bits(32)
    # index of the operation just completed by branch, and whether it is valid
    br_rob_idx: mk_bits(clog2(ROB_SIZE))
    br_rob_complete: mk_bits(1)
    br_target: mk_bits(32) # the target address
    br_mispredict: mk_bits(1) # whether the branch was mispredicted
    br_tag: mk_bits(clog2(NUM_BRANCHES)) # the tag of the branch

    # def __str__(self) -> str:
    #     return f"Int: {self.int_rob_idx}|{self.int_rob_complete}|{self.int_data} Load: {self.load_rob_idx}|{self.load_rob_complete}|{self.load_data} Store: {self.store_rob_idx}|{self.store_mem_q_idx}|{self.store_rob_complete}|{self.store_addr}|{self.store_data}"
