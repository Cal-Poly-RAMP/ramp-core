# fibonacci sequence
	addi	x5,	x0,	0
	addi	x6,	x0,	1
	li	x8,	0x11000000
	
back:	add	x7,	x5,	x6
	addi	x5,	x6,	0
	addi	x6,	x7,	0
	
	sw	x5,	(x8)
	addi	x8,	x8,	4
	
	bge	x6,	x0,	back
