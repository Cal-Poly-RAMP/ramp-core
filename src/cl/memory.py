from pymtl3 import *
import numpy as np

# A generic interface for memory. Variable address, data, word widths
class Memory(Component):
    def construct(s, addr_width, data_width, word_width):
        s.data_width = data_width
        s.addr_width = addr_width
        s.word_width = word_width

        # s.mem = [Bits(data_width) for _ in range(2**addr_width)] #TODO: implement as numpy array
        s.mem = np.zeros(2**addr_width, dtype="i8")

    # Return the value of the memory at the given address
    def read_word(s, addr: int) -> Bits:
        dpw = s.word_width // s.data_width
        if addr < 0 or addr >= 2**s.addr_width - dpw:
            raise IndexError("Address out of range")
        # return concat(*s.mem[addr : addr + dpw])
        return concat(*(Bits(s.data_width, x) for x in s.mem[addr : addr + dpw]))

    # Write the given value to the memory at the given address
    def write_word(s, addr: int, data: int) -> Bits:
        dpw = s.word_width // s.data_width
        s.mem[addr : addr + dpw] = [
            data[i * s.data_width : (i + 1) * s.data_width]
            for i in range(dpw - 1, -1, -1)
        ]

    # Load a .csv file to memory
    def load_file(s, filename: str):
        with open(filename, "r") as f:
            d = f.read().replace("\n", "").replace(" ", "").split(",")
            d = [Bits(s.data_width, x) for x in d if x]

            if len(d) == len(s.mem):
                s.mem = d
            else:
                raise ValueError("File size does not match memory size")

    # Save memory to a .csv file
    def save_file(s, filename: str):
        with open(filename, "w") as f:
            for i in range(len(s.mem)):
                f.write(str(int(s.mem[i])) + ",")

    def __str__(s):
        return str(s.mem)
