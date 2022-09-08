from pymtl3 import *
from src.cl.ramp_core import RampCore

def scalar_multiply(niter):
    # test unconditional jump without worrying about register renaming
    dut = RampCore(memory_size=niter)
    dut.apply(DefaultPassGroup(linetrace=False, vcdwave="vcd/test_ramp_core_scalar_multiply"))
    dut.sim_reset()

    # Load Program - endless fibonacci loop
    dut.fetch_stage.icache.load_file("tests/input_files/test_scalar_multiply.bin")

    # initializing dram
    for i in range(niter):
        dut.memory_unit.dram.mem[i] <<= i

    # running program, until it is finished
    idx_reg = dut.decode.register_rename.map_table[0x8]
    val_reg = dut.decode.register_rename.map_table[0x6]
    c = 0
    try:
        while dut.register_file.regs[idx_reg] < niter*4:
            # print("cycle:", c,
            #         "prd:", dut.register_file.regs[idx_reg],
            #         "val:", dut.register_file.regs[val_reg].uint(),
            #         end = "\r")
            print(c, [x.uint() for x in dut.register_file.regs])
            idx_reg = dut.decode.register_rename.map_table[0x8]
            val_reg = dut.decode.register_rename.map_table[0x6]
            dut.sim_tick()
            c += 1
    except:
        # while not input("continue: \r"):
        #     dut.sim_tick()

        # checking results
        for i in range(niter):
            try:
                assert dut.memory_unit.dram.mem[i] == i * 10
            except AssertionError:
                print([x.uint() for x in dut.memory_unit.dram.mem])
                print(c)
                assert dut.memory_unit.dram.mem[i] == i * 10

if __name__ == "__main__":
    scalar_multiply(1024)