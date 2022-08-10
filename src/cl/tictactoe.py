m, w, c, b, X, O, P, D, F = -1, 0, 0, "-" * 9, "X", "O", "X", "-", "{a}{s}{a}{s}{a}"
while not w and "-" in b:
    print(f"{b[0:3]}\n{b[3:6]}\n{b[6:9]}\n")
    while m < 0 or m > 9 or b[m] != "-":
        m = int(input("Move (0-8): "))
    b = b[:m] + P + b[m + 1 :]
    P = "O" if P == "X" else "X"
    for i in range(8):
        a = ["", "X", "O", "-"]
        B = "X" if i % 2 else "O"
        C = "{}{}{}{}{}{}{}{}{}"
        w = (C.format(B,a[i % 4],a[i // 4 % 4],a[i // 16 % 4],B,a[i // 64 % 4],a[i // 256 % 4],a[i // 1024 % 4],B,)in bor w)

