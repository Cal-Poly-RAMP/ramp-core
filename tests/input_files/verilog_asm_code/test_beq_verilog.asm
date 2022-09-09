# summing up all even numbers and odd numbers
	addi	x5,	zero,	0	# counter
	addi	x6,	zero,	0	# odd counter
	addi	x7,	zero,	0	# even counter
	addi	x9,	zero,	11	# max value
	
LOOP:	andi	x8,	x5,	1
	bge	x5,	x9,	END
	beq	x8,	zero,	EVEN
ODD:	add	x6,	x6,	x5
	addi	x5,	x5,	1
	andi	x8,	x5,	1
	j	LOOP
EVEN:	add	x7,	x7,	x5
	addi	x5,	x5,	1
	andi	x8,	x5,	1
	j	LOOP
END:	j	END