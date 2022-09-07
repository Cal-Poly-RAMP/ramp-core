from pymtl3 import Bits
import csv
import numpy as np


def one_hot(n: int, i: int) -> Bits:
    """
    One hot encoder.
    n: bitlen to output
    i: input index
    """
    if n < 1:
        raise ValueError("n must be greater than 0")
    if i < 0 or i >= n:
        raise ValueError("i must be between 0 and n-1")

    return Bits(n, 1) << i

def get_mem(filename, size):
    with open(filename, "rb") as f:
        mem = np.fromfile(f, dtype="u1", count=size)
        mem = np.pad(mem, (0, size - mem.size), "constant", constant_values=(0))
        mem = [Bits(8, x) for x in mem]

    return mem