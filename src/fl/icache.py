from pymtl3 import *
from src.fl.memory import Memory

# Generic interface for an instruction cache. Variable address, data, word widths
class ICache(Component):
    def construct(s, addr_width=16, word_width=64, data_width=8):
        # defining interface
        s.addr_width = addr_width
        s.word_width = word_width
        s.data_width = data_width
        s.addr = InPort(addr_width)  # TODO: increase size. smaller for simulation
        s.data_out = OutPort(word_width)  # two instructions

        s.memory = Memory(
            addr_width=s.addr_width, data_width=s.data_width, word_width=s.word_width
        )

        # connecting components
        @update
        def updt():
            s.data_out @= s.memory.read_word(s.addr)

    # overloading functions from memory
    def load_file(s, filename):
        s.memory.load_file(filename)

    def read_word(s, addr):
        return s.memory.read_word(addr)

    def write_word(s, addr, data):
        s.memory.write_word(addr, data)

    def line_trace(s):
        return "Addr: {} Data Out: {}".format(s.addr, s.data_out)
