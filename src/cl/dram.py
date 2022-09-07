from pymtl3 import (
    Component,
    InPort,
    OutPort,
    clog2,
    update,
    update_ff,
    Wire,
    mk_bits,
    Bits1,
)

# TODO: make byte addressable

class DRAM(Component):
    def construct(
        s, Type, num_entries=32, rd_ports=1, wr_ports=1, reset_value=0
    ):
        addr_type = mk_bits(max(1, clog2(num_entries)))

        s.raddr = [InPort(addr_type) for _ in range(rd_ports)]
        s.rdata = [OutPort(Type) for _ in range(rd_ports)]

        s.waddr = [InPort(addr_type) for _ in range(wr_ports)]
        s.wdata = [InPort(Type) for _ in range(wr_ports)]
        s.wen = [InPort(Bits1) for _ in range(wr_ports)]

        s.mem = [Wire(Type) for _ in range(num_entries)]

        # for byte addressable memory
        addr_shift = clog2(Type.nbits >> 3)

        @update
        def up_rf_read():
            for i in range(rd_ports):
                # TODO: CL debugging
                # assert not (s.raddr[i] % (Type.nbits // 8)), f"Address must be {Type.nbits // 8}-byte aligned"
                # byte addressable
                s.rdata[i] @= s.mem[s.raddr[i] >> addr_shift]

        @update_ff
        def up_rf_write():
            if s.reset:
                for i in range(num_entries):
                    s.mem[i] <<= reset_value
            else:
                for i in range(wr_ports):
                    if s.wen[i]:
                        # TODO: CL debugging
                        # assert not (s.waddr[i] % (Type.nbits // 8)), f"Address must be {Type.nbits // 8}-byte aligned"
                        s.mem[s.waddr[i] >> addr_shift] <<= s.wdata[i]

    def line_trace(s):
        nshown = min(32, len(s.mem))
        more = len(s.mem) - nshown
        return f"DRAM: {[hex(e.uint()) for e in s.mem[0:nshown]]}(+{more} more)"
