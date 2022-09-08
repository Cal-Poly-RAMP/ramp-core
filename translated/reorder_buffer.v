//-------------------------------------------------------------------------
// ReorderBuffer.v
//-------------------------------------------------------------------------
// This file is generated by PyMTL SystemVerilog translation pass.

// PyMTL BitStruct BranchUpdate__target_32__mispredict_1__tag_3 Definition
typedef struct packed {
  logic [31:0] target;
  logic [0:0] mispredict;
  logic [2:0] tag;
} BranchUpdate__target_32__mispredict_1__tag_3;

// PyMTL BitStruct ROBEntryUop__0a11cf2a2340c105 Definition
typedef struct packed {
  logic [0:0] valid;
  logic [0:0] busy;
  logic [2:0] optype;
  logic [5:0] prd;
  logic [5:0] stale;
  logic [31:0] data;
  logic [3:0] mem_q_idx;
  logic [31:0] store_addr;
  logic [31:0] br_target;
  logic [2:0] br_tag;
  logic [0:0] br_mispredict;
  logic [7:0] br_mask;
} ROBEntryUop__0a11cf2a2340c105;

// PyMTL BitStruct ROBEntry__dfb4245d7bc69416 Definition
typedef struct packed {
  logic [31:0] pc;
  ROBEntryUop__0a11cf2a2340c105 uop1_entry;
  ROBEntryUop__0a11cf2a2340c105 uop2_entry;
} ROBEntry__dfb4245d7bc69416;

// PyMTL BitStruct ExecToROB__894aaf470679b4c5 Definition
typedef struct packed {
  logic [4:0] int_rob_idx;
  logic [0:0] int_rob_complete;
  logic [31:0] int_data;
  logic [4:0] load_rob_idx;
  logic [0:0] load_rob_complete;
  logic [31:0] load_data;
  logic [4:0] store_rob_idx;
  logic [3:0] store_mem_q_idx;
  logic [0:0] store_rob_complete;
  logic [31:0] store_addr;
  logic [31:0] store_data;
  logic [4:0] br_rob_idx;
  logic [0:0] br_rob_complete;
  logic [31:0] br_target;
  logic [0:0] br_mispredict;
  logic [2:0] br_tag;
} ExecToROB__894aaf470679b4c5;

// PyMTL BitStruct MicroOp__38e2b09b91e4b306 Definition
typedef struct packed {
  logic [2:0] optype;
  logic [31:0] inst;
  logic [31:0] pc;
  logic [0:0] valid;
  logic [4:0] lrd;
  logic [4:0] lrs1;
  logic [4:0] lrs2;
  logic [5:0] prd;
  logic [5:0] prs1;
  logic [5:0] prs2;
  logic [5:0] stale;
  logic [31:0] imm;
  logic [1:0] issue_unit;
  logic [1:0] funct_unit;
  logic [3:0] funct_op;
  logic [0:0] branch_taken;
  logic [7:0] br_mask;
  logic [2:0] br_tag;
  logic [4:0] rob_idx;
  logic [3:0] mem_q_idx;
} MicroOp__38e2b09b91e4b306;

// PyMTL BitStruct DualMicroOp__93e30b890d7542af Definition
typedef struct packed {
  MicroOp__38e2b09b91e4b306 uop1;
  MicroOp__38e2b09b91e4b306 uop2;
} DualMicroOp__93e30b890d7542af;

// PyMTL Component ReorderBuffer Definition
// Full name: ReorderBuffer_noparam
// At /Users/curtisbucher/Desktop/ramp-core/src/cl/reorder_buffer.py

module ReorderBuffer
(
  output logic [0:0] bank_empty ,
  output logic [0:0] bank_full ,
  input  logic [0:0] clk ,
  output ROBEntry__dfb4245d7bc69416 commit_out ,
  input  ExecToROB__894aaf470679b4c5 op_complete ,
  input  logic [0:0] reset ,
  output logic [4:0] rob_tail ,
  input  DualMicroOp__93e30b890d7542af write_in ,
  input logic [0:0] br_update__en  ,
  input BranchUpdate__target_32__mispredict_1__tag_3 br_update__msg  ,
  output logic [0:0] br_update__rdy  
);
  localparam ROBEntryUop__0a11cf2a2340c105 __const__empty_rob_entry_at_comb_  = { 1'd0, 1'd0, 3'd0, 6'd0, 6'd0, 32'd0, 4'd0, 32'd0, 32'd0, 3'd0, 1'd0, 8'd0 };
  localparam logic [5:0] __const__ROB_SIZE  = 6'd32;
  localparam logic [0:0] __const__one_at_comb_  = 1'd1;
  ROBEntry__dfb4245d7bc69416 instr_bank [0:15];
  ROBEntry__dfb4245d7bc69416 instr_bank_next [0:15];
  logic [3:0] internal_rob_head;
  logic [3:0] internal_rob_head_next;
  logic [3:0] internal_rob_tail;
  logic [3:0] internal_rob_tail_next;
  ROBEntryUop__0a11cf2a2340c105 uop1_entry;
  ROBEntryUop__0a11cf2a2340c105 uop1_entry_next;
  ROBEntryUop__0a11cf2a2340c105 uop2_entry;
  ROBEntryUop__0a11cf2a2340c105 uop2_entry_next;
  logic [3:0] __tmpvar__comb__internal_int_rob_addr;
  logic [3:0] __tmpvar__comb__internal_load_rob_addr;
  logic [3:0] __tmpvar__comb__internal_store_rob_addr;
  logic [3:0] __tmpvar__comb__internal_br_rob_addr;
  logic [7:0] __tmpvar__comb__tag_mask;

  // PyMTL Update Block Source
  // At /Users/curtisbucher/Desktop/ramp-core/src/cl/reorder_buffer.py:72
  // @update
  // def comb_():
  //     # indexed so that uop1 is at odd indices and uop2 is at even indices
  //     s.rob_tail @= sext(s.internal_rob_tail << 1, rob_addr_nbits)
  // 
  //     # bank full if head == tail and value is busy
  //     s.bank_full @= (
  //         (s.internal_rob_head == s.internal_rob_tail)
  //         & s.instr_bank[s.internal_rob_tail].uop1_entry.busy
  //         & s.instr_bank[s.internal_rob_tail].uop2_entry.busy
  //     )
  // 
  //     # bank empty if head == tail and value is invalid(TODO: ?)
  //     s.bank_empty @= (s.internal_rob_head == s.internal_rob_tail) & ~(
  //         s.instr_bank[s.internal_rob_tail].uop1_entry.busy
  //         | s.instr_bank[s.internal_rob_tail].uop2_entry.busy
  //     )
  // 
  //     # defaults
  //     s.internal_rob_head_next @= s.internal_rob_head
  //     s.internal_rob_tail_next @= s.internal_rob_tail
  //     s.uop1_entry_next @= empty_rob_entry
  //     s.uop1_entry_next @= empty_rob_entry
  //     for i in range(ROB_SIZE >> 1):
  //         s.instr_bank_next[i] @= s.instr_bank[i]
  // 
  //     # WRITING TO ROB
  //     # if either of the uops is valid, and there is room in the buffer,
  //     # write both to the ROB
  //     if s.write_in.uop1.valid | s.write_in.uop2.valid:
  //         # if the circular buffer is not full
  //         # TODO: assert for CL
  //         # assert ~s.bank_full, "ROB is full and tried to write"
  //         s.instr_bank_next[s.internal_rob_tail] @= ROBEntry(
  //             s.write_in.uop1.pc,                 # PC
  //             ROBEntryUop(                        # uop1
  //                 s.write_in.uop1.valid,          # valid
  //                 s.write_in.uop1.valid,          # busy
  //                 s.write_in.uop1.optype,         # optype
  //                 s.write_in.uop1.prd,            # prd
  //                 s.write_in.uop1.stale,          # stale
  //                 0,                              # data
  //                 0,                              # mem_q_idx
  //                 0,                              # store_addr
  //                 0,                              # br_target
  //                 0,                              # br_tag
  //                 0,                              # br_mispredict
  //                 s.write_in.uop1.br_mask,        # br_mask
  //             ),
  //             ROBEntryUop(                        # uop2
  //                 s.write_in.uop2.valid,          # valid
  //                 s.write_in.uop2.valid,          # busy
  //                 s.write_in.uop2.optype,         # optype
  //                 s.write_in.uop2.prd,            # prd
  //                 s.write_in.uop2.stale,          # stale
  //                 0,                              # data
  //                 0,                              # mem_q_idx
  //                 0,                              # store_addr
  //                 0,                              # br_target
  //                 0,                              # br_tag
  //                 0,                              # br_mispredict
  //                 s.write_in.uop2.br_mask,        # br_mask
  //             ),
  //         )
  //         s.internal_rob_tail_next @= s.internal_rob_tail + 1  # wrap around
  // 
  //     # UPDATING COMPLETED UOPS
  //     # even though actual instruction bank is 2 wide,
  //     # uop1 and uop2 are indexed seperately (even and odd respectively)
  //     # rob indices must be calculated from these indices in the uop
  // 
  //     # INTEGER UPDATES
  //     internal_int_rob_addr = trunc(s.op_complete.int_rob_idx >> 1, instr_bank_addr_nbits)
  //     if s.op_complete.int_rob_complete:
  //         if s.op_complete.int_rob_idx % 2 == 0:
  //             # even index, uop1 is completed
  //             s.instr_bank_next[internal_int_rob_addr].uop1_entry.busy @= 0
  //             s.instr_bank_next[
  //                 internal_int_rob_addr
  //             ].uop1_entry.data @= s.op_complete.int_data
  //         else:
  //             # odd index, uop2 is completed
  //             s.instr_bank_next[internal_int_rob_addr].uop2_entry.busy @= 0
  //             s.instr_bank_next[
  //                 internal_int_rob_addr
  //             ].uop2_entry.data @= s.op_complete.int_data
  // 
  //     # LOAD UPDATES
  //     internal_load_rob_addr = trunc(s.op_complete.load_rob_idx >> 1, instr_bank_addr_nbits)
  //     if s.op_complete.load_rob_complete:
  //         if s.op_complete.load_rob_idx % 2 == 0:
  //             # even index, uop1 is completed
  //             s.instr_bank_next[internal_load_rob_addr].uop1_entry.busy @= 0
  //             s.instr_bank_next[
  //                 internal_load_rob_addr
  //             ].uop1_entry.data @= s.op_complete.load_data
  //         else:
  //             # odd index, uop2 is completed
  //             s.instr_bank_next[internal_load_rob_addr].uop2_entry.busy @= 0
  //             s.instr_bank_next[
  //                 internal_load_rob_addr
  //             ].uop2_entry.data @= s.op_complete.load_data
  // 
  //     # STORE UPDATES
  //     internal_store_rob_addr = trunc(s.op_complete.store_rob_idx >> 1, instr_bank_addr_nbits)
  //     if s.op_complete.store_rob_complete:
  //         if s.op_complete.store_rob_idx % 2 == 0:
  //             # even index, uop1 is completed
  //             s.instr_bank_next[internal_store_rob_addr].uop1_entry.busy @= 0
  //             s.instr_bank_next[
  //                 internal_store_rob_addr
  //             ].uop1_entry.data @= s.op_complete.store_data
  //             s.instr_bank_next[
  //                 internal_store_rob_addr
  //             ].uop1_entry.store_addr @= s.op_complete.store_addr
  //             s.instr_bank_next[
  //                 internal_store_rob_addr
  //             ].uop1_entry.mem_q_idx @= s.op_complete.store_mem_q_idx
  //         else:
  //             # odd index, uop2 is completed
  //             s.instr_bank_next[internal_store_rob_addr].uop2_entry.busy @= 0
  //             s.instr_bank_next[
  //                 internal_store_rob_addr
  //             ].uop2_entry.data @= s.op_complete.store_data
  //             s.instr_bank_next[
  //                 internal_store_rob_addr
  //             ].uop2_entry.store_addr @= s.op_complete.store_addr
  //             s.instr_bank_next[
  //                 internal_store_rob_addr
  //             ].uop2_entry.mem_q_idx @= s.op_complete.store_mem_q_idx
  // 
  //     # BRANCH UPDATES
  //     internal_br_rob_addr = trunc(s.op_complete.br_rob_idx >> 1, instr_bank_addr_nbits)
  //     if s.op_complete.br_rob_complete:
  //         if s.op_complete.br_rob_idx % 2 == 0:
  //             # even index, uop1 is completed
  //             s.instr_bank_next[internal_br_rob_addr].uop1_entry.busy @= 0
  //             s.instr_bank_next[
  //                 internal_br_rob_addr
  //             ].uop1_entry.br_target @= s.op_complete.br_target
  //             s.instr_bank_next[
  //                 internal_br_rob_addr
  //             ].uop1_entry.br_tag @= s.op_complete.br_tag
  //             s.instr_bank_next[
  //                 internal_br_rob_addr
  //             ].uop1_entry.br_mispredict @= s.op_complete.br_mispredict
  //         else:
  //             # odd index, uop2 is completed
  //             s.instr_bank_next[internal_br_rob_addr].uop2_entry.busy @= 0
  //             s.instr_bank_next[
  //                 internal_br_rob_addr
  //             ].uop2_entry.br_target @= s.op_complete.br_target
  //             s.instr_bank_next[
  //                 internal_br_rob_addr
  //             ].uop2_entry.br_tag @= s.op_complete.br_tag
  //             s.instr_bank_next[
  //                 internal_br_rob_addr
  //             ].uop2_entry.br_mispredict @= s.op_complete.br_mispredict
  // 
  //     # BRANCH PREDICTION UPDATES (updating tags with branch outcomes)
  //     tag_mask = zext(one, NUM_BRANCHES) << zext(s.br_update.msg.tag, NUM_BRANCHES)
  // 
  //     if s.br_update.en:
  //         for i in range(ROB_SIZE >> 1):
  //             # if the branch was predicted correctly, update bitmask
  //             if ~s.br_update.msg.mispredict:
  //                 s.instr_bank_next[i].uop1_entry.br_mask @= (
  //                     s.instr_bank[i].uop1_entry.br_mask & ~tag_mask
  //                 )
  //                 s.instr_bank_next[i].uop2_entry.br_mask @= (
  //                     s.instr_bank[i].uop2_entry.br_mask & ~tag_mask
  //                 )
  //             # if the branch was predicted incorrectly robentry is dependent on branch
  //             # invalidate robentry
  //             else:
  //                 if s.instr_bank[i].uop1_entry.br_mask & tag_mask:
  //                     s.instr_bank_next[i].uop1_entry.valid @= 0
  //                     s.instr_bank_next[i].uop1_entry.busy @= 0
  //                 if s.instr_bank[i].uop2_entry.br_mask & tag_mask:
  //                     s.instr_bank_next[i].uop2_entry.valid @= 0
  //                     s.instr_bank_next[i].uop2_entry.busy @= 0
  // 
  //     # COMMITTING
  //     # committed store instructions write to memory
  //     # committed arithmetic instructions deallocate stale reg
  // 
  //     # if the ROB's head entry uop1 is valid, not busy, and not under speculation, commit
  //     if (
  //         s.instr_bank_next[s.internal_rob_head_next].uop1_entry.valid
  //         & ~s.instr_bank_next[s.internal_rob_head_next].uop1_entry.busy
  //         & (s.instr_bank_next[s.internal_rob_head_next].uop1_entry.br_mask == 0)
  //     ):
  //         s.uop1_entry_next @= s.instr_bank_next[
  //             s.internal_rob_head_next
  //         ].uop1_entry
  //         s.instr_bank_next[s.internal_rob_head_next].uop1_entry.valid @= 0
  //     # otherwise do not commit it
  //     else:
  //         s.uop1_entry_next @= empty_rob_entry
  //     # if the ROB's head entry uop2 is valid and not busy, commit it
  //     if (
  //         s.instr_bank_next[s.internal_rob_head_next].uop2_entry.valid
  //         & ~s.instr_bank_next[s.internal_rob_head_next].uop2_entry.busy
  //         & (s.instr_bank_next[s.internal_rob_head_next].uop1_entry.br_mask == 0)
  //     ):
  //         s.uop2_entry_next @= s.instr_bank_next[
  //             s.internal_rob_head_next
  //         ].uop2_entry
  //         s.instr_bank_next[s.internal_rob_head_next].uop2_entry.valid @= 0
  //     # otherwise do not commit it
  //     else:
  //         s.uop2_entry_next @= empty_rob_entry
  // 
  //     # if the ROB's head entry is not busy (committed), deallocate it
  //     if (
  //         ~s.instr_bank_next[s.internal_rob_head_next].uop1_entry.valid
  //         & ~s.instr_bank_next[s.internal_rob_head_next].uop2_entry.valid
  //     ):
  //         # if the circular buffer is not empty
  //         if ~s.bank_empty:
  //             s.internal_rob_head_next @= s.internal_rob_head_next + 1
  //         # else:
  //         #     raise Exception("ROB is empty, and tried to deallocate")
  // 
  // 
  //     # ASYNCHRONOUS RESET
  //     if s.reset:
  //         s.internal_rob_head_next @= 0
  //         s.internal_rob_tail_next @= 0
  //         s.uop1_entry_next @= empty_rob_entry
  //         s.uop1_entry_next @= empty_rob_entry
  // 
  //         for i in range(ROB_SIZE >> 1):
  //             s.instr_bank_next[i].uop1_entry.valid @= 0
  //             s.instr_bank_next[i].uop2_entry.valid @= 0
  //             s.instr_bank_next[i].uop1_entry.busy @= 0
  //             s.instr_bank_next[i].uop2_entry.busy @= 0
  
  always_comb begin : comb_
    rob_tail = { { 1 { internal_rob_tail << 1'd1[3] } }, internal_rob_tail << 1'd1 };
    bank_full = ( ( internal_rob_head == internal_rob_tail ) & instr_bank[internal_rob_tail].uop1_entry.busy ) & instr_bank[internal_rob_tail].uop2_entry.busy;
    bank_empty = ( internal_rob_head == internal_rob_tail ) & ( ~( instr_bank[internal_rob_tail].uop1_entry.busy | instr_bank[internal_rob_tail].uop2_entry.busy ) );
    internal_rob_head_next = internal_rob_head;
    internal_rob_tail_next = internal_rob_tail;
    uop1_entry_next = 129'( __const__empty_rob_entry_at_comb_ );
    uop1_entry_next = 129'( __const__empty_rob_entry_at_comb_ );
    for ( int unsigned i = 1'd0; i < 6'( __const__ROB_SIZE ) >> 1'd1; i += 1'd1 )
      instr_bank_next[4'(i)] = instr_bank[4'(i)];
    if ( write_in.uop1.valid | write_in.uop2.valid ) begin
      instr_bank_next[internal_rob_tail] = { write_in.uop1.pc, { write_in.uop1.valid, write_in.uop1.valid, write_in.uop1.optype, write_in.uop1.prd, write_in.uop1.stale, 32'd0, 4'd0, 32'd0, 32'd0, 3'd0, 1'd0, write_in.uop1.br_mask }, { write_in.uop2.valid, write_in.uop2.valid, write_in.uop2.optype, write_in.uop2.prd, write_in.uop2.stale, 32'd0, 4'd0, 32'd0, 32'd0, 3'd0, 1'd0, write_in.uop2.br_mask } };
      internal_rob_tail_next = internal_rob_tail + 4'd1;
    end
    __tmpvar__comb__internal_int_rob_addr = 4'(op_complete.int_rob_idx >> 1'd1);
    if ( op_complete.int_rob_complete ) begin
      if ( ( op_complete.int_rob_idx % 5'd2 ) == 5'd0 ) begin
        instr_bank_next[__tmpvar__comb__internal_int_rob_addr].uop1_entry.busy = 1'd0;
        instr_bank_next[__tmpvar__comb__internal_int_rob_addr].uop1_entry.data = op_complete.int_data;
      end
      else begin
        instr_bank_next[__tmpvar__comb__internal_int_rob_addr].uop2_entry.busy = 1'd0;
        instr_bank_next[__tmpvar__comb__internal_int_rob_addr].uop2_entry.data = op_complete.int_data;
      end
    end
    __tmpvar__comb__internal_load_rob_addr = 4'(op_complete.load_rob_idx >> 1'd1);
    if ( op_complete.load_rob_complete ) begin
      if ( ( op_complete.load_rob_idx % 5'd2 ) == 5'd0 ) begin
        instr_bank_next[__tmpvar__comb__internal_load_rob_addr].uop1_entry.busy = 1'd0;
        instr_bank_next[__tmpvar__comb__internal_load_rob_addr].uop1_entry.data = op_complete.load_data;
      end
      else begin
        instr_bank_next[__tmpvar__comb__internal_load_rob_addr].uop2_entry.busy = 1'd0;
        instr_bank_next[__tmpvar__comb__internal_load_rob_addr].uop2_entry.data = op_complete.load_data;
      end
    end
    __tmpvar__comb__internal_store_rob_addr = 4'(op_complete.store_rob_idx >> 1'd1);
    if ( op_complete.store_rob_complete ) begin
      if ( ( op_complete.store_rob_idx % 5'd2 ) == 5'd0 ) begin
        instr_bank_next[__tmpvar__comb__internal_store_rob_addr].uop1_entry.busy = 1'd0;
        instr_bank_next[__tmpvar__comb__internal_store_rob_addr].uop1_entry.data = op_complete.store_data;
        instr_bank_next[__tmpvar__comb__internal_store_rob_addr].uop1_entry.store_addr = op_complete.store_addr;
        instr_bank_next[__tmpvar__comb__internal_store_rob_addr].uop1_entry.mem_q_idx = op_complete.store_mem_q_idx;
      end
      else begin
        instr_bank_next[__tmpvar__comb__internal_store_rob_addr].uop2_entry.busy = 1'd0;
        instr_bank_next[__tmpvar__comb__internal_store_rob_addr].uop2_entry.data = op_complete.store_data;
        instr_bank_next[__tmpvar__comb__internal_store_rob_addr].uop2_entry.store_addr = op_complete.store_addr;
        instr_bank_next[__tmpvar__comb__internal_store_rob_addr].uop2_entry.mem_q_idx = op_complete.store_mem_q_idx;
      end
    end
    __tmpvar__comb__internal_br_rob_addr = 4'(op_complete.br_rob_idx >> 1'd1);
    if ( op_complete.br_rob_complete ) begin
      if ( ( op_complete.br_rob_idx % 5'd2 ) == 5'd0 ) begin
        instr_bank_next[__tmpvar__comb__internal_br_rob_addr].uop1_entry.busy = 1'd0;
        instr_bank_next[__tmpvar__comb__internal_br_rob_addr].uop1_entry.br_target = op_complete.br_target;
        instr_bank_next[__tmpvar__comb__internal_br_rob_addr].uop1_entry.br_tag = op_complete.br_tag;
        instr_bank_next[__tmpvar__comb__internal_br_rob_addr].uop1_entry.br_mispredict = op_complete.br_mispredict;
      end
      else begin
        instr_bank_next[__tmpvar__comb__internal_br_rob_addr].uop2_entry.busy = 1'd0;
        instr_bank_next[__tmpvar__comb__internal_br_rob_addr].uop2_entry.br_target = op_complete.br_target;
        instr_bank_next[__tmpvar__comb__internal_br_rob_addr].uop2_entry.br_tag = op_complete.br_tag;
        instr_bank_next[__tmpvar__comb__internal_br_rob_addr].uop2_entry.br_mispredict = op_complete.br_mispredict;
      end
    end
    __tmpvar__comb__tag_mask = { { 7 { 1'b0 } }, 1'( __const__one_at_comb_ ) } << { { 5 { 1'b0 } }, br_update__msg.tag };
    if ( br_update__en ) begin
      for ( int unsigned i = 1'd0; i < 6'( __const__ROB_SIZE ) >> 1'd1; i += 1'd1 )
        if ( ~br_update__msg.mispredict ) begin
          instr_bank_next[4'(i)].uop1_entry.br_mask = instr_bank[4'(i)].uop1_entry.br_mask & ( ~__tmpvar__comb__tag_mask );
          instr_bank_next[4'(i)].uop2_entry.br_mask = instr_bank[4'(i)].uop2_entry.br_mask & ( ~__tmpvar__comb__tag_mask );
        end
        else begin
          if ( instr_bank[4'(i)].uop1_entry.br_mask & __tmpvar__comb__tag_mask ) begin
            instr_bank_next[4'(i)].uop1_entry.valid = 1'd0;
            instr_bank_next[4'(i)].uop1_entry.busy = 1'd0;
          end
          if ( instr_bank[4'(i)].uop2_entry.br_mask & __tmpvar__comb__tag_mask ) begin
            instr_bank_next[4'(i)].uop2_entry.valid = 1'd0;
            instr_bank_next[4'(i)].uop2_entry.busy = 1'd0;
          end
        end
    end
    if ( ( instr_bank_next[internal_rob_head_next].uop1_entry.valid & ( ~instr_bank_next[internal_rob_head_next].uop1_entry.busy ) ) & ( instr_bank_next[internal_rob_head_next].uop1_entry.br_mask == 8'd0 ) ) begin
      uop1_entry_next = instr_bank_next[internal_rob_head_next].uop1_entry;
      instr_bank_next[internal_rob_head_next].uop1_entry.valid = 1'd0;
    end
    else
      uop1_entry_next = 129'( __const__empty_rob_entry_at_comb_ );
    if ( ( instr_bank_next[internal_rob_head_next].uop2_entry.valid & ( ~instr_bank_next[internal_rob_head_next].uop2_entry.busy ) ) & ( instr_bank_next[internal_rob_head_next].uop1_entry.br_mask == 8'd0 ) ) begin
      uop2_entry_next = instr_bank_next[internal_rob_head_next].uop2_entry;
      instr_bank_next[internal_rob_head_next].uop2_entry.valid = 1'd0;
    end
    else
      uop2_entry_next = 129'( __const__empty_rob_entry_at_comb_ );
    if ( ( ~instr_bank_next[internal_rob_head_next].uop1_entry.valid ) & ( ~instr_bank_next[internal_rob_head_next].uop2_entry.valid ) ) begin
      if ( ~bank_empty ) begin
        internal_rob_head_next = internal_rob_head_next + 4'd1;
      end
    end
    if ( reset ) begin
      internal_rob_head_next = 4'd0;
      internal_rob_tail_next = 4'd0;
      uop1_entry_next = 129'( __const__empty_rob_entry_at_comb_ );
      uop1_entry_next = 129'( __const__empty_rob_entry_at_comb_ );
      for ( int unsigned i = 1'd0; i < 6'( __const__ROB_SIZE ) >> 1'd1; i += 1'd1 ) begin
        instr_bank_next[4'(i)].uop1_entry.valid = 1'd0;
        instr_bank_next[4'(i)].uop2_entry.valid = 1'd0;
        instr_bank_next[4'(i)].uop1_entry.busy = 1'd0;
        instr_bank_next[4'(i)].uop2_entry.busy = 1'd0;
      end
    end
  end

  // PyMTL Update Block Source
  // At /Users/curtisbucher/Desktop/ramp-core/src/cl/reorder_buffer.py:310
  // @update_ff
  // def sync_():
  //     s.internal_rob_head <<= s.internal_rob_head_next
  //     s.internal_rob_tail <<= s.internal_rob_tail_next
  //     s.uop1_entry <<= s.uop1_entry_next
  //     s.uop2_entry <<= s.uop2_entry_next
  //     for i in range(ROB_SIZE >> 1):
  //         s.instr_bank[i] <<= s.instr_bank_next[i]
  
  always_ff @(posedge clk) begin : sync_
    internal_rob_head <= internal_rob_head_next;
    internal_rob_tail <= internal_rob_tail_next;
    uop1_entry <= uop1_entry_next;
    uop2_entry <= uop2_entry_next;
    for ( int unsigned i = 1'd0; i < 6'( __const__ROB_SIZE ) >> 1'd1; i += 1'd1 )
      instr_bank[4'(i)] <= instr_bank_next[4'(i)];
  end

  assign commit_out.uop1_entry = uop1_entry;
  assign commit_out.uop2_entry = uop2_entry;
  assign br_update__rdy = 1'd1;

endmodule