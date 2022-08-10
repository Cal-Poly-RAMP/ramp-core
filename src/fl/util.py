from pymtl3 import Bits
from typing import List


def cascading_priority_encoder(n: int, word: Bits) -> List[int]:
    """
    Cascading priority encoder.
    n: number elements to output
    input: input vector
    out_bits: the output bitwidth

    note:   if there are no high bits, the output will be all zeros
            which is the same as if the input had 0 bit set
            to remedy, must check that any bits are set seperately
    """
    if n < 1:
        raise ValueError("n must be greater than 0")
    if word.nbits < n:
        raise ValueError("number of bits in word must be greater than or equal to n")

    encoded = [0] * n
    c = 0
    for i in range(word.nbits):
        if word[i]:
            encoded[c] = i
            c += 1
            if c == n:
                break

    return encoded


def one_hot(n: int, i: int) -> Bits:
    """
    One hot encoder.
    n: number elements to output
    i: input index
    """
    if n < 1:
        raise ValueError("n must be greater than 0")
    if i < 0 or i >= n:
        raise ValueError("i must be between 0 and n-1")

    return Bits(n, 1) << i
