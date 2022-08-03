//-------------------------------------------------------------------------
// SingleInstDecode.v
//-------------------------------------------------------------------------
// This file is generated by PyMTL SystemVerilog translation pass.

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

// PyMTL BitStruct MicroOp__32db6ace22edd734 Definition
typedef struct packed {
  logic [3:0] uop_code;
  logic [31:0] inst;
  logic [31:0] pc;
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
} MicroOp__32db6ace22edd734;

// PyMTL Component SingleInstDecode Definition
// Full name: SingleInstDecode_noparam
// At /Users/curtisbucher/Desktop/ramp-core/src/cl/decoder.py

module SingleInstDecode
(
  input  logic [0:0] clk ,
  input  logic [31:0] inst ,
  input  PhysicalRegs__prd_6__prs1_6__prs2_6__stale_6 pregs ,
  input  PRegBusy__prs1_1__prs2_1 pregs_busy ,
  input  logic [0:0] reset ,
  output MicroOp__32db6ace22edd734 uop 
);
  localparam logic [2:0] __const__RD_BEG  = 3'd7;
  localparam logic [3:0] __const__RD_END  = 4'd12;
  localparam logic [3:0] __const__RS1_BEG  = 4'd15;
  localparam logic [4:0] __const__RS1_END  = 5'd20;
  localparam logic [4:0] __const__RS2_BEG  = 5'd20;
  localparam logic [4:0] __const__RS2_END  = 5'd25;
  logic [6:0] __tmpvar__decode_comb_opcode;
  logic [0:0] __tmpvar__decode_comb_Rtype;
  logic [0:0] __tmpvar__decode_comb_Itype;
  logic [0:0] __tmpvar__decode_comb_Stype;
  logic [0:0] __tmpvar__decode_comb_Btype;
  logic [0:0] __tmpvar__decode_comb_Utype;
  logic [0:0] __tmpvar__decode_comb_Jtype;
  logic [0:0] __tmpvar__decode_comb_Csrtype;

  // PyMTL Update Block Source
  // At /Users/curtisbucher/Desktop/ramp-core/src/cl/decoder.py:94
  // @update
  // def decode_comb():
  //     # For determining type
  //     opcode = s.inst[0:7]
  // 
  //     Rtype = opcode == 0b0110011
  //     Itype = (
  //         (opcode == 0b0010011) | (opcode == 0b0000011) | (opcode == 0b1100111)
  //     )
  //     Stype = opcode == 0b0100011
  //     Btype = opcode == 0b1100011
  //     Utype = (opcode == 0b0110111) | (opcode == 0b0010111)
  //     Jtype = opcode == 0b1101111
  //     Csrtype = opcode == 0b1110011
  // 
  //     # uop (hardcoded values)
  //     s.uop.inst @= s.inst
  //     s.uop.pc @= 0  # TODO
  // 
  //     s.uop.lrd @= s.inst[RD_BEG:RD_END]
  //     s.uop.lrs1 @= s.inst[RS1_BEG:RS1_END]
  //     s.uop.lrs2 @= s.inst[RS2_BEG:RS2_END]
  // 
  //     s.uop.prd @= s.pregs.prd
  //     s.uop.prs1 @= s.pregs.prs1
  //     s.uop.prs2 @= s.pregs.prs2
  //     s.uop.stale @= s.pregs.stale
  // 
  //     # s.uop.prd_busy @= s.register_rename.busy_table[
  //     #     s.uop.prd
  //     # ]  # should always be true, do i need this?
  //     s.uop.prs1_busy @= s.pregs_busy.prs1
  //     s.uop.prs2_busy @= s.pregs_busy.prs2
  // 
  //     # immediates
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
    __tmpvar__decode_comb_Rtype = __tmpvar__decode_comb_opcode == 7'd51;
    __tmpvar__decode_comb_Itype = ( ( __tmpvar__decode_comb_opcode == 7'd19 ) | ( __tmpvar__decode_comb_opcode == 7'd3 ) ) | ( __tmpvar__decode_comb_opcode == 7'd103 );
    __tmpvar__decode_comb_Stype = __tmpvar__decode_comb_opcode == 7'd35;
    __tmpvar__decode_comb_Btype = __tmpvar__decode_comb_opcode == 7'd99;
    __tmpvar__decode_comb_Utype = ( __tmpvar__decode_comb_opcode == 7'd55 ) | ( __tmpvar__decode_comb_opcode == 7'd23 );
    __tmpvar__decode_comb_Jtype = __tmpvar__decode_comb_opcode == 7'd111;
    __tmpvar__decode_comb_Csrtype = __tmpvar__decode_comb_opcode == 7'd115;
    uop.inst = inst;
    uop.pc = 32'd0;
    uop.lrd = inst[5'd11:5'( __const__RD_BEG )];
    uop.lrs1 = inst[5'd19:5'( __const__RS1_BEG )];
    uop.lrs2 = inst[5'd24:5'( __const__RS2_BEG )];
    uop.prd = pregs.prd;
    uop.prs1 = pregs.prs1;
    uop.prs2 = pregs.prs2;
    uop.stale = pregs.stale;
    uop.prs1_busy = pregs_busy.prs1;
    uop.prs2_busy = pregs_busy.prs2;
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
