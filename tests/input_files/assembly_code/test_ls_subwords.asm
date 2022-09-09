# testing lb, lh, lbu, lhu (assumes 0xdeadbeef loaded at mem[0])
li	x1,	0xdeadbeef
li	x2,	0x6004
sb	x1,	-4(x2)	# 0x000000ef
sh	x1,	0(x2)	# 0x0000beef
sw	x1,	4(x2)	# 0xdeadbeef

lb	x3,	4(x2)	# 0xffffffef
lh	x4,	4(x2)	# 0xffffbeef
lw	x5,	4(x2)	# 0xdeadbeef

lbu	x6,	4(x2)	# 0x000000ef
lhu	x7,	4(x2)	# 0x0000beef