## Program to multiply by 50
## (6 << 7 + c << 5 + 6 << 2) >> 1
ori	t0,	x0,	6
andi	t1,	t0,	2
addi	t2,	x0,	5
addi	t3,	x0,	7

sll	t1,	t0,	t1
sll	t2,	t0, 	t2
sll	t3,	t0,	t3

sub	t0,	t3,	t2
add	t0,	t1,	t0

srai	t0,	t0,	1


