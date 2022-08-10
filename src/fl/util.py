from pymtl3 import Bits

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
