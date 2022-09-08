//-------------------------------------------------------------------------
// DRAM.v
//-------------------------------------------------------------------------
// This file is generated by PyMTL SystemVerilog translation pass.

// PyMTL Component DRAM Definition
// Full name: DRAM__Type_Bits32__num_entries_32__rd_ports_1__wr_ports_1__reset_value_0
// At /Users/curtisbucher/Desktop/ramp-core/src/cl/dram.py

module DRAM
(
  input  logic [0:0] clk ,
  input  logic [4:0] raddr [0:0],
  output logic [31:0] rdata [0:0],
  input  logic [0:0] reset ,
  input  logic [4:0] waddr [0:0],
  input  logic [31:0] wdata [0:0],
  input  logic [0:0] wen [0:0]
);
  localparam logic [0:0] __const__rd_ports_at_up_rf_read  = 1'd1;
  localparam logic [1:0] __const__addr_shift_at_up_rf_read  = 2'd2;
  localparam logic [5:0] __const__num_entries_at_up_rf_write  = 6'd32;
  localparam logic [0:0] __const__reset_value_at_up_rf_write  = 1'd0;
  localparam logic [0:0] __const__wr_ports_at_up_rf_write  = 1'd1;
  localparam logic [1:0] __const__addr_shift_at_up_rf_write  = 2'd2;
  logic [31:0] mem [0:31];

  // PyMTL Update Block Source
  // At /Users/curtisbucher/Desktop/ramp-core/src/cl/dram.py:33
  // @update
  // def up_rf_read():
  //     for i in range(rd_ports):
  //         # TODO: CL debugging
  //         # assert not (s.raddr[i] % (Type.nbits // 8)), f"Address must be {Type.nbits // 8}-byte aligned"
  //         # byte addressable
  //         s.rdata[i] @= s.mem[s.raddr[i] >> addr_shift]
  
  always_comb begin : up_rf_read
    for ( int unsigned i = 1'd0; i < 1'( __const__rd_ports_at_up_rf_read ); i += 1'd1 )
      rdata[1'(i)] = mem[raddr[1'(i)] >> 2'( __const__addr_shift_at_up_rf_read )];
  end

  // PyMTL Update Block Source
  // At /Users/curtisbucher/Desktop/ramp-core/src/cl/dram.py:41
  // @update_ff
  // def up_rf_write():
  //     if s.reset:
  //         for i in range(num_entries):
  //             s.mem[i] <<= reset_value
  //     else:
  //         for i in range(wr_ports):
  //             if s.wen[i]:
  //                 # TODO: CL debugging
  //                 # assert not (s.waddr[i] % (Type.nbits // 8)), f"Address must be {Type.nbits // 8}-byte aligned"
  //                 s.mem[s.waddr[i] >> addr_shift] <<= s.wdata[i]
  
  always_ff @(posedge clk) begin : up_rf_write
    if ( reset ) begin
      for ( int unsigned i = 1'd0; i < 6'( __const__num_entries_at_up_rf_write ); i += 1'd1 )
        mem[5'(i)] <= 32'( __const__reset_value_at_up_rf_write );
    end
    else
      for ( int unsigned i = 1'd0; i < 1'( __const__wr_ports_at_up_rf_write ); i += 1'd1 )
        if ( wen[1'(i)] ) begin
          mem[waddr[1'(i)] >> 2'( __const__addr_shift_at_up_rf_write )] <= wdata[1'(i)];
        end
  end

endmodule