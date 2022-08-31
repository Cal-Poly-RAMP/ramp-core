from pymtl3 import Bits
import csv


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


def csv_to_vector(csv_file: str) -> list:
    """
    Convert a CSV file to a list of lists.
    """
    with open("tests/input_files/test_ramp_core_vector.csv") as f:
        csvreader = csv.reader(f)
        header = [h.strip() for h in next(csvreader) if h]
        rows = []
        for row in csvreader:
            rows.append([_to_int(r) for r in row if r])

    return [header] + rows


def _to_int(x):
    if x.strip() == "?":
        return "?"
    elif "x" in x:
        return int(x, 16)
    elif "b" in x:
        return int(x, 2)
    else:
        return int(x)
