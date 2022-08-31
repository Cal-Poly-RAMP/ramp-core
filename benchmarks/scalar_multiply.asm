# This program iterates over an array of 1024 numbers, multiplying each element by 10 in place
# Curtis Bucher

# load data address (s0) and array index (t0)
	li	s0,	0x6000
	li	s1,	0x7000
	
START: 	lw	t1,	0x0(s0)
	slli	t2,	t1,	3
	slli	t3,	t1,	1
	add	t1,	t2,	t3
	sw	t1,	0x0(s0)
	addi	s0,	s0,	4
	bne 	s0,	s1,	START
