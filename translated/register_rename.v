//-------------------------------------------------------------------------
// RegisterRename.v
//-------------------------------------------------------------------------
// This file is generated by PyMTL SystemVerilog translation pass.

// PyMTL BitStruct LogicalRegs__lrd_5__lrs1_5__lrs2_5 Definition
typedef struct packed {
  logic [4:0] lrd;
  logic [4:0] lrs1;
  logic [4:0] lrs2;
} LogicalRegs__lrd_5__lrs1_5__lrs2_5;

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

// PyMTL Component RegisterRename Definition
// Full name: RegisterRename_noparam
// At /Users/curtisbucher/Desktop/ramp-core/src/cl/register_rename.py

module RegisterRename
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
