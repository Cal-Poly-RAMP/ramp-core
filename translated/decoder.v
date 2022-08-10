//-------------------------------------------------------------------------
// Decode.v
//-------------------------------------------------------------------------
// This file is generated by PyMTL SystemVerilog translation pass.

// PyMTL BitStruct MicroOp__8aebb2d496e39e44 Definition
typedef struct packed {
  logic [2:0] type;
  logic [31:0] inst;
  logic [7:0] pc;
  logic [0:0] valid;
  logic [4:0] lrd;
  logic [4:0] lrs1;
  logic [4:0] lrs2;
  logic [5:0] prd;
  logic [5:0] prs1;
  logic [5:0] prs2;
  logic [5:0] stale;
  logic [0:0] prs1_busy;
  logic [0:0] prs2_busy;
  logic [31:0] imm;
  logic [1:0] issue_unit;
  logic [1:0] fu_unit;
  logic [1:0] fu_op;
  logic [4:0] rob_idx;
} MicroOp__8aebb2d496e39e44;

// PyMTL BitStruct DualMicroOp__225a29605d3739d4 Definition
typedef struct packed {
  MicroOp__8aebb2d496e39e44 uop1;
  MicroOp__8aebb2d496e39e44 uop2;
} DualMicroOp__225a29605d3739d4;

// PyMTL BitStruct FetchPacket__inst1_32__inst2_32__pc_8 Definition
typedef struct packed {
  logic [31:0] inst1;
  logic [31:0] inst2;
  logic [7:0] pc;
} FetchPacket__inst1_32__inst2_32__pc_8;

// PyMTL BitStruct PhysicalRegs__prd_6__prs1_6__prs2_6__stale_6 Definition
typedef struct packed {
  logic [5:0] prd;
  logic [5:0] prs1;
  logic [5:0] prs2;
  logic [5:0] stale;
} PhysicalRegs__prd_6__prs1_6__prs2_6__stale_6;

// PyMTL BitStruct PRegBusy__prs1_1__prs2_1 Definition
typedef struct packed {
  logic [0:0] prs1;
  logic [0:0] prs2;
} PRegBusy__prs1_1__prs2_1;

// PyMTL BitStruct LogicalRegs__lrd_5__lrs1_5__lrs2_5 Definition
typedef struct packed {
  logic [4:0] lrd;
  logic [4:0] lrs1;
  logic [4:0] lrs2;
} LogicalRegs__lrd_5__lrs1_5__lrs2_5;

// PyMTL Component SingleInstDecode Definition
// At /Users/curtisbucher/Desktop/ramp-core/src/cl/decoder.py

module SingleInstDecode_noparam
(
  input  logic [0:0] clk ,
  input  logic [31:0] inst ,
  input  logic [7:0] pc ,
  input  PhysicalRegs__prd_6__prs1_6__prs2_6__stale_6 pregs ,
  input  PRegBusy__prs1_1__prs2_1 pregs_busy ,
  input  logic [0:0] reset ,
  output MicroOp__8aebb2d496e39e44 uop 
);
  localparam logic [5:0] __const__RTYPE_OPCODE  = 6'd51;
  localparam logic [4:0] __const__ITYPE_OPCODE1  = 5'd19;
  localparam logic [1:0] __const__ITYPE_OPCODE2  = 2'd3;
  localparam logic [6:0] __const__ITYPE_OPCODE3  = 7'd103;
  localparam logic [5:0] __const__STYPE_OPCODE  = 6'd35;
  localparam logic [6:0] __const__BTYPE_OPCODE  = 7'd99;
  localparam logic [5:0] __const__UTYPE_OPCODE1  = 6'd55;
  localparam logic [4:0] __const__UTYPE_OPCODE2  = 5'd23;
  localparam logic [6:0] __const__JTYPE_OPCODE  = 7'd111;
  localparam logic [6:0] __const__CSRTYPE_OPCODE  = 7'd115;
  localparam logic [0:0] __const__INT_ISSUE_UNIT  = 1'd1;
  localparam logic [1:0] __const__MEM_ISSUE_UNIT  = 2'd2;
  logic [6:0] __tmpvar__decode_comb_opcode;
  logic [0:0] __tmpvar__decode_comb_Rtype;
  logic [0:0] __tmpvar__decode_comb_Itype;
  logic [0:0] __tmpvar__decode_comb_Stype;
  logic [0:0] __tmpvar__decode_comb_Btype;
  logic [0:0] __tmpvar__decode_comb_Utype;
  logic [0:0] __tmpvar__decode_comb_Jtype;
  logic [0:0] __tmpvar__decode_comb_Csrtype;
  logic [0:0] __tmpvar__decode_comb_mem_issue;
  logic [0:0] __tmpvar__decode_comb_int_issue;

  // PyMTL Update Block Source
  // At /Users/curtisbucher/Desktop/ramp-core/src/cl/decoder.py:143
  // @update
  // def decode_comb():
  //     # For determining type
  //     opcode = s.inst[0:7]
  // 
  //     Rtype = opcode == RTYPE_OPCODE
  //     Itype = (
  //         (opcode == ITYPE_OPCODE1)
  //         | (opcode == ITYPE_OPCODE2)
  //         | (opcode == ITYPE_OPCODE3)
  //     )
  //     Stype = opcode == STYPE_OPCODE
  //     Btype = opcode == BTYPE_OPCODE
  //     Utype = (opcode == UTYPE_OPCODE1) | (opcode == UTYPE_OPCODE2)
  //     Jtype = opcode == JTYPE_OPCODE
  //     Csrtype = opcode == CSRTYPE_OPCODE
  // 
  //     # For determining issue unit
  //     mem_issue = (opcode == ITYPE_OPCODE2) | (opcode == STYPE_OPCODE)
  //     int_issue = ~mem_issue  # TODO: fpu issue
  // 
  //     # uop (hardcoded values)
  //     # TODO: uopcode
  //     s.uop.inst @= s.inst
  //     s.uop.pc @= (s.pc + 4) if s.idx else (s.pc)
  //     s.uop.valid @= 1
  // 
  //     s.uop.lrd @= s.inst[RD_SLICE]
  //     s.uop.lrs1 @= s.inst[RS1_SLICE]
  //     s.uop.lrs2 @= s.inst[RS2_SLICE]
  // 
  //     s.uop.prd @= s.pregs.prd
  //     s.uop.prs1 @= s.pregs.prs1
  //     s.uop.prs2 @= s.pregs.prs2
  //     s.uop.stale @= s.pregs.stale
  // 
  //     s.uop.prs1_busy @= s.pregs_busy.prs1
  //     s.uop.prs2_busy @= s.pregs_busy.prs2
  // 
  //     s.uop.issue_unit @= (
  //         INT_ISSUE_UNIT if int_issue else MEM_ISSUE_UNIT if mem_issue else 0
  //     )
  // 
  //     # immediates TODO: update with slices
  //     if Rtype:
  //         s.uop.imm @= 0
  //     elif Itype:
  //         s.uop.imm @= sext(s.inst[20:32], 32)
  //         s.uop.lrs2 @= 0
  //     elif Stype:
  //         s.uop.imm @= sext(concat(s.inst[25:32], s.inst[7:12]), 32)
  //         s.uop.lrd @= 0
  //     elif Btype:
  //         s.uop.imm @= sext(
  //             concat(
  //                 s.inst[31], s.inst[7], s.inst[25:31], s.inst[8:12], Bits1(0)
  //             ),
  //             32,
  //         )
  //         s.uop.lrd @= 0
  //     elif Utype:
  //         s.uop.imm @= concat(s.inst[12:32], Bits12(0))
  //         s.uop.lrs1 @= 0
  //         s.uop.lrs2 @= 0
  //     elif Jtype:
  //         s.uop.imm @= sext(
  //             concat(
  //                 s.inst[31],
  //                 s.inst[12:20],
  //                 s.inst[20],
  //                 s.inst[25:31],
  //                 s.inst[21:25],
  //                 Bits1(0),
  //             ),
  //             32,
  //         )
  //         s.uop.lrs1 @= 0
  //         s.uop.lrs2 @= 0
  //     elif Csrtype:
  //         s.uop.imm @= 0
  //         s.uop.lrs2 @= 0
  
  always_comb begin : decode_comb
    __tmpvar__decode_comb_opcode = inst[5'd6:5'd0];
    __tmpvar__decode_comb_Rtype = __tmpvar__decode_comb_opcode == 7'( __const__RTYPE_OPCODE );
    __tmpvar__decode_comb_Itype = ( ( __tmpvar__decode_comb_opcode == 7'( __const__ITYPE_OPCODE1 ) ) | ( __tmpvar__decode_comb_opcode == 7'( __const__ITYPE_OPCODE2 ) ) ) | ( __tmpvar__decode_comb_opcode == 7'( __const__ITYPE_OPCODE3 ) );
    __tmpvar__decode_comb_Stype = __tmpvar__decode_comb_opcode == 7'( __const__STYPE_OPCODE );
    __tmpvar__decode_comb_Btype = __tmpvar__decode_comb_opcode == 7'( __const__BTYPE_OPCODE );
    __tmpvar__decode_comb_Utype = ( __tmpvar__decode_comb_opcode == 7'( __const__UTYPE_OPCODE1 ) ) | ( __tmpvar__decode_comb_opcode == 7'( __const__UTYPE_OPCODE2 ) );
    __tmpvar__decode_comb_Jtype = __tmpvar__decode_comb_opcode == 7'( __const__JTYPE_OPCODE );
    __tmpvar__decode_comb_Csrtype = __tmpvar__decode_comb_opcode == 7'( __const__CSRTYPE_OPCODE );
    __tmpvar__decode_comb_mem_issue = ( __tmpvar__decode_comb_opcode == 7'( __const__ITYPE_OPCODE2 ) ) | ( __tmpvar__decode_comb_opcode == 7'( __const__STYPE_OPCODE ) );
    __tmpvar__decode_comb_int_issue = ~__tmpvar__decode_comb_mem_issue;
    uop.inst = inst;
    uop.pc = 1'd0 ? pc + 8'd4 : pc;
    uop.valid = 1'd1;
    uop.lrd = inst[5'd11:5'd7];
    uop.lrs1 = inst[5'd19:5'd15];
    uop.lrs2 = inst[5'd24:5'd20];
    uop.prd = pregs.prd;
    uop.prs1 = pregs.prs1;
    uop.prs2 = pregs.prs2;
    uop.stale = pregs.stale;
    uop.prs1_busy = pregs_busy.prs1;
    uop.prs2_busy = pregs_busy.prs2;
    uop.issue_unit = __tmpvar__decode_comb_int_issue ? 2'( __const__INT_ISSUE_UNIT ) : __tmpvar__decode_comb_mem_issue ? 2'( __const__MEM_ISSUE_UNIT ) : 2'd0;
    if ( __tmpvar__decode_comb_Rtype ) begin
      uop.imm = 32'd0;
    end
    else if ( __tmpvar__decode_comb_Itype ) begin
      uop.imm = { { 20 { inst[5'd31] } }, inst[5'd31:5'd20] };
      uop.lrs2 = 5'd0;
    end
    else if ( __tmpvar__decode_comb_Stype ) begin
      uop.imm = { { 20 { { inst[5'd31:5'd25], inst[5'd11:5'd7] }[11] } }, { inst[5'd31:5'd25], inst[5'd11:5'd7] } };
      uop.lrd = 5'd0;
    end
    else if ( __tmpvar__decode_comb_Btype ) begin
      uop.imm = { { 19 { { inst[5'd31], inst[5'd7], inst[5'd30:5'd25], inst[5'd11:5'd8], 1'd0 }[12] } }, { inst[5'd31], inst[5'd7], inst[5'd30:5'd25], inst[5'd11:5'd8], 1'd0 } };
      uop.lrd = 5'd0;
    end
    else if ( __tmpvar__decode_comb_Utype ) begin
      uop.imm = { inst[5'd31:5'd12], 12'd0 };
      uop.lrs1 = 5'd0;
      uop.lrs2 = 5'd0;
    end
    else if ( __tmpvar__decode_comb_Jtype ) begin
      uop.imm = { { 11 { { inst[5'd31], inst[5'd19:5'd12], inst[5'd20], inst[5'd30:5'd25], inst[5'd24:5'd21], 1'd0 }[20] } }, { inst[5'd31], inst[5'd19:5'd12], inst[5'd20], inst[5'd30:5'd25], inst[5'd24:5'd21], 1'd0 } };
      uop.lrs1 = 5'd0;
      uop.lrs2 = 5'd0;
    end
    else if ( __tmpvar__decode_comb_Csrtype ) begin
      uop.imm = 32'd0;
      uop.lrs2 = 5'd0;
    end
  end

endmodule


// PyMTL Component RegisterRename Definition
// At /Users/curtisbucher/Desktop/ramp-core/src/cl/register_rename.py

module RegisterRename_noparam
(
  output logic [63:0] busy_table ,
  input  logic [0:0] clk ,
  output logic [63:0] free_list ,
  input  LogicalRegs__lrd_5__lrs1_5__lrs2_5 inst1_lregs ,
  output PhysicalRegs__prd_6__prs1_6__prs2_6__stale_6 inst1_pregs ,
  output PRegBusy__prs1_1__prs2_1 inst1_pregs_busy ,
  input  LogicalRegs__lrd_5__lrs1_5__lrs2_5 inst2_lregs ,
  output PhysicalRegs__prd_6__prs1_6__prs2_6__stale_6 inst2_pregs ,
  output PRegBusy__prs1_1__prs2_1 inst2_pregs_busy ,
  input  logic [0:0] reset 
);
  localparam logic [2:0] __const__PHYS_REG_BITWIDTH  = 3'd6;
  localparam logic [5:0] __const__NUM_ISA_REGS  = 6'd32;
  logic [63:0] busy_table_next;
  logic [63:0] free_list_next;
  logic [5:0] map_table [0:31];
  logic [5:0] map_table_wr1;
  logic [5:0] map_table_wr2;
  logic [5:0] pdst1;
  logic [5:0] pdst2;

  // PyMTL Update Block Source
  // At /Users/curtisbucher/Desktop/ramp-core/src/cl/register_rename.py:77
  // @update
  // def rename_comb():
  //     # Combinatorially getting physical source registers from map table
  //     # and getting physical dest registers from free list
  //     # TODO: add assert statements for when physical registers are full
  // 
  //     # *combinatorially* getting dest registers, but not updating tables
  //     # pdst1, pdst2 = cascading_priority_encoder(2, s.free_list_next)
  //     s.pdst1 @= 0
  //     s.pdst2 @= 0
  //     for i in range(PHYS_REG_BITWIDTH):
  //         if s.free_list[i]:
  //             if s.pdst1 == 0:
  //                 s.pdst1 @= i
  //             elif s.pdst2 == 0:
  //                 s.pdst2 @= i
  //     # making sure that there are free registers
  //     # assert s.pdst1 != 0 or s.pdst2 != 0
  // 
  //     if s.inst1_lregs.lrd:
  //         s.inst1_pregs.prd @= s.pdst1
  //         s.inst2_pregs.prd @= s.pdst2 if s.inst2_lregs.lrd else 0
  //     elif s.inst2_lregs.lrd:
  //         s.inst1_pregs.prd @= 0
  //         s.inst2_pregs.prd @= s.pdst1
  //     else:
  //         s.inst1_pregs.prd @= 0
  //         s.inst2_pregs.prd @= 0
  // 
  //     s.inst1_pregs.prs1 @= s.map_table[s.inst1_lregs.lrs1]
  //     s.inst1_pregs.prs2 @= s.map_table[s.inst1_lregs.lrs2]
  //     s.inst1_pregs.stale @= s.map_table[s.inst1_lregs.lrd]
  //     s.inst1_pregs_busy.prs1 @= s.busy_table[s.inst1_pregs.prs1]
  //     s.inst1_pregs_busy.prs2 @= s.busy_table[s.inst1_pregs.prs2]
  // 
  //     # bypass network.
  //     # forward dependent sources from inst2 to inst1. handle stale
  //     if (s.inst2_lregs.lrd == s.inst1_lregs.lrd) & (s.inst1_lregs.lrd != 0):
  //         # inst2 dependent on inst1.
  //         s.inst2_pregs.stale @= s.pdst1
  //     else:
  //         s.inst2_pregs.stale @= s.map_table[s.inst2_lregs.lrd]
  // 
  //     if (s.inst2_lregs.lrs1 == s.inst1_lregs.lrd) & (s.inst1_lregs.lrd != 0):
  //         # inst2 dependent on inst1. inst2 prs1 = pdst1 and is busy
  //         s.inst2_pregs.prs1 @= s.pdst1
  //         s.inst2_pregs_busy.prs1 @= 1
  //     else:
  //         s.inst2_pregs.prs1 @= s.map_table[s.inst2_lregs.lrs1]
  //         s.inst2_pregs_busy.prs1 @= s.busy_table[s.inst2_pregs.prs2]
  // 
  //     if (s.inst2_lregs.lrs2 == s.inst1_lregs.lrd) & (s.inst1_lregs.lrd != 0):
  //         # inst2 dependent on inst1. inst2 prs2 = pdst1 and is busy
  //         s.inst2_pregs.prs2 @= s.pdst1
  //         s.inst2_pregs_busy.prs2 @= 1
  //     else:
  //         s.inst2_pregs.prs2 @= s.map_table[s.inst2_lregs.lrs2]
  //         s.inst2_pregs_busy.prs2 @= s.busy_table[s.inst2_pregs.prs2]
  // 
  //     # nextstate for updating free_list, map_table, busy_table
  //     if s.reset:
  //         s.free_list_next @= s.free_list_reset
  //         s.busy_table_next @= 0
  //     else:
  //         # updating tables with newely allocated registers
  //         if (s.inst1_lregs.lrd != 0) ^ (s.inst2_lregs.lrd != 0):
  //             s.free_list_next @= s.free_list_next & ~(
  //                 s.ONE << zext(s.pdst1, NUM_PHYS_REGS)
  //             )
  //             s.busy_table_next @= s.busy_table | (
  //                 s.ONE << zext(s.pdst1, NUM_PHYS_REGS)
  //             )
  //             if s.inst1_lregs.lrd:
  //                 s.map_table_wr1 @= s.pdst1
  //             elif s.inst2_lregs.lrd:
  //                 s.map_table_wr2 @= s.pdst1
  // 
  //         elif (s.inst1_lregs.lrd != 0) & (s.inst2_lregs.lrd != 0):
  //             # ensuring there are registers to allocate
  //             s.free_list_next @= (
  //                 s.free_list_next
  //                 & ~(s.ONE << zext(s.pdst1, NUM_PHYS_REGS))
  //                 & ~(s.ONE << zext(s.pdst2, NUM_PHYS_REGS))
  //             )
  //             s.busy_table_next @= (
  //                 s.busy_table
  //                 | s.ONE << zext(s.pdst1, NUM_PHYS_REGS)
  //                 | s.ONE << zext(s.pdst2, NUM_PHYS_REGS)
  //             )
  //             s.map_table_wr1 @= s.pdst1
  //             s.map_table_wr2 @= s.pdst2
  
  always_comb begin : rename_comb
    pdst1 = 6'd0;
    pdst2 = 6'd0;
    for ( int unsigned i = 1'd0; i < 3'( __const__PHYS_REG_BITWIDTH ); i += 1'd1 )
      if ( free_list[6'(i)] ) begin
        if ( pdst1 == 6'd0 ) begin
          pdst1 = 6'(i);
        end
        else if ( pdst2 == 6'd0 ) begin
          pdst2 = 6'(i);
        end
      end
    if ( inst1_lregs.lrd ) begin
      inst1_pregs.prd = pdst1;
      inst2_pregs.prd = inst2_lregs.lrd ? pdst2 : 6'd0;
    end
    else if ( inst2_lregs.lrd ) begin
      inst1_pregs.prd = 6'd0;
      inst2_pregs.prd = pdst1;
    end
    else begin
      inst1_pregs.prd = 6'd0;
      inst2_pregs.prd = 6'd0;
    end
    inst1_pregs.prs1 = map_table[inst1_lregs.lrs1];
    inst1_pregs.prs2 = map_table[inst1_lregs.lrs2];
    inst1_pregs.stale = map_table[inst1_lregs.lrd];
    inst1_pregs_busy.prs1 = busy_table[inst1_pregs.prs1];
    inst1_pregs_busy.prs2 = busy_table[inst1_pregs.prs2];
    if ( ( inst2_lregs.lrd == inst1_lregs.lrd ) & ( inst1_lregs.lrd != 5'd0 ) ) begin
      inst2_pregs.stale = pdst1;
    end
    else
      inst2_pregs.stale = map_table[inst2_lregs.lrd];
    if ( ( inst2_lregs.lrs1 == inst1_lregs.lrd ) & ( inst1_lregs.lrd != 5'd0 ) ) begin
      inst2_pregs.prs1 = pdst1;
      inst2_pregs_busy.prs1 = 1'd1;
    end
    else begin
      inst2_pregs.prs1 = map_table[inst2_lregs.lrs1];
      inst2_pregs_busy.prs1 = busy_table[inst2_pregs.prs2];
    end
    if ( ( inst2_lregs.lrs2 == inst1_lregs.lrd ) & ( inst1_lregs.lrd != 5'd0 ) ) begin
      inst2_pregs.prs2 = pdst1;
      inst2_pregs_busy.prs2 = 1'd1;
    end
    else begin
      inst2_pregs.prs2 = map_table[inst2_lregs.lrs2];
      inst2_pregs_busy.prs2 = busy_table[inst2_pregs.prs2];
    end
    if ( reset ) begin
      free_list_next = 64'd18446744073709551614;
      busy_table_next = 64'd0;
    end
    else if ( ( inst1_lregs.lrd != 5'd0 ) ^ ( inst2_lregs.lrd != 5'd0 ) ) begin
      free_list_next = free_list_next & ( ~( 64'd1 << { { 58 { 1'b0 } }, pdst1 } ) );
      busy_table_next = busy_table | ( 64'd1 << { { 58 { 1'b0 } }, pdst1 } );
      if ( inst1_lregs.lrd ) begin
        map_table_wr1 = pdst1;
      end
      else if ( inst2_lregs.lrd ) begin
        map_table_wr2 = pdst1;
      end
    end
    else if ( ( inst1_lregs.lrd != 5'd0 ) & ( inst2_lregs.lrd != 5'd0 ) ) begin
      free_list_next = ( free_list_next & ( ~( 64'd1 << { { 58 { 1'b0 } }, pdst1 } ) ) ) & ( ~( 64'd1 << { { 58 { 1'b0 } }, pdst2 } ) );
      busy_table_next = ( busy_table | ( 64'd1 << { { 58 { 1'b0 } }, pdst1 } ) ) | ( 64'd1 << { { 58 { 1'b0 } }, pdst2 } );
      map_table_wr1 = pdst1;
      map_table_wr2 = pdst2;
    end
  end

  // PyMTL Update Block Source
  // At /Users/curtisbucher/Desktop/ramp-core/src/cl/register_rename.py:169
  // @update_ff
  // def rename_ff():
  //     s.free_list <<= s.free_list_next
  //     s.busy_table <<= s.busy_table_next
  //     s.map_table[s.inst1_lregs.lrd] <<= s.map_table_wr1
  //     s.map_table[s.inst2_lregs.lrd] <<= s.map_table_wr2
  // 
  //     # # resetting
  //     if s.reset == 1:
  //         for x in range(NUM_ISA_REGS):
  //             s.map_table[x] <<= 0
  
  always_ff @(posedge clk) begin : rename_ff
    free_list <= free_list_next;
    busy_table <= busy_table_next;
    map_table[inst1_lregs.lrd] <= map_table_wr1;
    map_table[inst2_lregs.lrd] <= map_table_wr2;
    if ( reset == 1'd1 ) begin
      for ( int unsigned x = 1'd0; x < 6'( __const__NUM_ISA_REGS ); x += 1'd1 )
        map_table[5'(x)] <= 6'd0;
    end
  end

endmodule


// PyMTL Component Decode Definition
// Full name: Decode_noparam
// At /Users/curtisbucher/Desktop/ramp-core/src/cl/decoder.py

module Decode
(
  output logic [63:0] busy_table ,
  input  logic [0:0] clk ,
  output DualMicroOp__225a29605d3739d4 dual_uop ,
  input  FetchPacket__inst1_32__inst2_32__pc_8 fetch_packet ,
  input  logic [0:0] reset 
);
  logic [31:0] inst1;
  logic [31:0] inst2;
  //-------------------------------------------------------------
  // Component d1
  //-------------------------------------------------------------

  logic [0:0] d1__clk;
  logic [31:0] d1__inst;
  logic [7:0] d1__pc;
  PhysicalRegs__prd_6__prs1_6__prs2_6__stale_6 d1__pregs;
  PRegBusy__prs1_1__prs2_1 d1__pregs_busy;
  logic [0:0] d1__reset;
  MicroOp__8aebb2d496e39e44 d1__uop;

  SingleInstDecode_noparam d1
  (
    .clk( d1__clk ),
    .inst( d1__inst ),
    .pc( d1__pc ),
    .pregs( d1__pregs ),
    .pregs_busy( d1__pregs_busy ),
    .reset( d1__reset ),
    .uop( d1__uop )
  );

  //-------------------------------------------------------------
  // End of component d1
  //-------------------------------------------------------------

  //-------------------------------------------------------------
  // Component d2
  //-------------------------------------------------------------

  logic [0:0] d2__clk;
  logic [31:0] d2__inst;
  logic [7:0] d2__pc;
  PhysicalRegs__prd_6__prs1_6__prs2_6__stale_6 d2__pregs;
  PRegBusy__prs1_1__prs2_1 d2__pregs_busy;
  logic [0:0] d2__reset;
  MicroOp__8aebb2d496e39e44 d2__uop;

  SingleInstDecode_noparam d2
  (
    .clk( d2__clk ),
    .inst( d2__inst ),
    .pc( d2__pc ),
    .pregs( d2__pregs ),
    .pregs_busy( d2__pregs_busy ),
    .reset( d2__reset ),
    .uop( d2__uop )
  );

  //-------------------------------------------------------------
  // End of component d2
  //-------------------------------------------------------------

  //-------------------------------------------------------------
  // Component register_rename
  //-------------------------------------------------------------

  logic [63:0] register_rename__busy_table;
  logic [0:0] register_rename__clk;
  logic [63:0] register_rename__free_list;
  LogicalRegs__lrd_5__lrs1_5__lrs2_5 register_rename__inst1_lregs;
  PhysicalRegs__prd_6__prs1_6__prs2_6__stale_6 register_rename__inst1_pregs;
  PRegBusy__prs1_1__prs2_1 register_rename__inst1_pregs_busy;
  LogicalRegs__lrd_5__lrs1_5__lrs2_5 register_rename__inst2_lregs;
  PhysicalRegs__prd_6__prs1_6__prs2_6__stale_6 register_rename__inst2_pregs;
  PRegBusy__prs1_1__prs2_1 register_rename__inst2_pregs_busy;
  logic [0:0] register_rename__reset;

  RegisterRename_noparam register_rename
  (
    .busy_table( register_rename__busy_table ),
    .clk( register_rename__clk ),
    .free_list( register_rename__free_list ),
    .inst1_lregs( register_rename__inst1_lregs ),
    .inst1_pregs( register_rename__inst1_pregs ),
    .inst1_pregs_busy( register_rename__inst1_pregs_busy ),
    .inst2_lregs( register_rename__inst2_lregs ),
    .inst2_pregs( register_rename__inst2_pregs ),
    .inst2_pregs_busy( register_rename__inst2_pregs_busy ),
    .reset( register_rename__reset )
  );

  //-------------------------------------------------------------
  // End of component register_rename
  //-------------------------------------------------------------

  assign inst1 = fetch_packet.inst1;
  assign inst2 = fetch_packet.inst2;
  assign d1__clk = clk;
  assign d1__reset = reset;
  assign d1__inst = inst1;
  assign d1__pc = fetch_packet.pc;
  assign dual_uop.uop1 = d1__uop;
  assign d2__clk = clk;
  assign d2__reset = reset;
  assign d2__inst = inst2;
  assign d2__pc = fetch_packet.pc;
  assign dual_uop.uop2 = d2__uop;
  assign register_rename__clk = clk;
  assign register_rename__reset = reset;
  assign register_rename__inst1_lregs.lrd = d1__uop.lrd;
  assign register_rename__inst1_lregs.lrs1 = d1__uop.lrs1;
  assign register_rename__inst1_lregs.lrs2 = d1__uop.lrs2;
  assign register_rename__inst2_lregs.lrd = d2__uop.lrd;
  assign register_rename__inst2_lregs.lrs1 = d2__uop.lrs1;
  assign register_rename__inst2_lregs.lrs2 = d2__uop.lrs2;
  assign d1__pregs.prd = register_rename__inst1_pregs.prd;
  assign d1__pregs.prs1 = register_rename__inst1_pregs.prs1;
  assign d1__pregs.prs2 = register_rename__inst1_pregs.prs2;
  assign d1__pregs.stale = register_rename__inst1_pregs.stale;
  assign d2__pregs.prd = register_rename__inst2_pregs.prd;
  assign d2__pregs.prs1 = register_rename__inst2_pregs.prs1;
  assign d2__pregs.prs2 = register_rename__inst2_pregs.prs2;
  assign d2__pregs.stale = register_rename__inst2_pregs.stale;
  assign d1__pregs_busy = register_rename__inst1_pregs_busy;
  assign d2__pregs_busy = register_rename__inst2_pregs_busy;
  assign busy_table = register_rename__busy_table;

endmodule
