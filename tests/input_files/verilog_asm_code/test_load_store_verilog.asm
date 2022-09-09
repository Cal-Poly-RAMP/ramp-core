# Loading immediate address
li	x1,	8
# Loading immediate data
li	x2, 	42
# Storing data to 10 + x1
sw	x2,	-4(x1)
# Loading data from addr to register
lw	x3,	-4(x1)
# adding both together
add	x4,	x2,	x3
