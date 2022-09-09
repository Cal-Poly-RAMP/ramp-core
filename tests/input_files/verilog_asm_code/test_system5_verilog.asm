## Program to multiply by 314
## (6 << 7 + c << 5 + 6 << 2) >> 1
li 	t0,	6

slli	t1, 	t0,	8
slli	t2, 	t0,	6
slli	t3, 	t0,	2
slli	t4, 	t0,	1

add	t1,	t1,	t2
add	t3,	t3,	t4
sub	t0,	t1,	t3

