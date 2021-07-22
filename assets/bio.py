#Alignment values
MATCH = 2
TRANSITON_MISS = -1
TRANSVERSION_MISS = -2
GAP = -16
EXTENSION = -1

'''
Checks the match quality between two strings using dynamic programming, then traverses backwards
	To determine the optimal alignment between the two of the based on the match quality
Input: A string, A string
Returns: A dictionary containing a string representing an alignment between the two strings (retrieved by the key BODY),
	and an integer representing the score of the alignment (retrieved by the key SCORE)
'''
def align(seq_1, seq_2):
	matrix = []
	for row in range(len(seq_1)+1):
	    col_list = []
	    for col in range(len(seq_2)+1):
	        col_list.append(0)
	    matrix.append(col_list)

	seq_1_char = ''
	seq_2_char = ''

	in_gap = False

	#Fill the matrix with the match quality of all substring combinations of the two strings
	for row in range(len(matrix)):
		for col in range(len(matrix[0])):
			if row != 0 or col != 0:
				current_max = float('-inf')
				miss_max = float('-inf')

				if row != 0:
					seq_1_char = seq_1[row-1]
				else:
					seq_1_char = '-'

				if col != 0:
					seq_2_char = seq_2[col-1]
				else:
					seq_2_char = '-'

				#If there's a match, the best option will always be to move diagonally
				if seq_2_char == seq_1_char:
					matrix[row][col] = matrix[row-1][col-1] + MATCH
				#Else, determine whether it's better overall to have a GAP, or to have a MISS
				else:
					if row != 0:
						current_max = max(current_max, matrix[row-1][col] + get_miss(in_gap))
					if col != 0:
						current_max = max(current_max, matrix[row][col-1] + get_miss(in_gap))
					if row !=0 and col != 0:
						miss_max = matrix[row-1][col-1] + get_mismatch(seq_1_char, seq_2_char)
						current_max = max(current_max, miss_max)

					matrix[row][col] = current_max

				if current_max == miss_max and not in_gap:
					in_gap = True
				elif current_max != miss_max and in_gap:
					in_gap = False

	score = matrix[len(seq_1)][len(seq_2)]

	row = len(seq_1)
	col = len(seq_2)

	#Traverse backwards based on the maximum value, inserting the characters into an array
	alignment = []
	alignment_char = seq_1[row-1]
	while row > 0 and col > 0:
		alignment.append(alignment_char)

		if row == 0:
			alignment_char = '-'
			col -= 1
		else:
			max_val = max(matrix[row-1][col-1], matrix[row-1][col], matrix[row][col-1])

			if max_val == matrix[row-1][col-1]:
				alignment_char = seq_2[col-2]
				row -= 1
				col -= 1
			else:
				alignment_char = '-'
				if max_val == matrix[row-1][col]:
					row -= 1
				else:
					col -= 1

	#Reverse the strings that were entered backwards
	alignment.reverse()

	#Convert from list of integers to string
	alignment = ''.join(str(e) for e in alignment)

	return {'sequence': alignment, 'score' : score}

'''
Checks the match quality of sequence x to sequence y using dynamic programming, then traverses backwards
	To determine the optimal alignment between the two of the based on the match quality
Input: A string, A string
Returns: A string representing an alignment of string x to string y
'''
def align_x_to_y(seq_x, seq_y):
	matrix = []
	for row in range(len(seq_x)+1):
	    col_list = []
	    for col in range(len(seq_y)+1):
	        col_list.append(0)
	    matrix.append(col_list)

	seq_x_char = ''
	seq_y_char = ''

	in_gap = False

	#Fill the matrix with the match quality of all substring combinations of the two strings
	for row in range(len(matrix)):
		for col in range(len(matrix[0])):
			if row != 0 or col != 0:
				current_max = float('-inf')
				miss_max = float('-inf')

				if row != 0:
					seq_x_char = seq_x[row-1]
				else:
					seq_x_char = '-'

				if col != 0:
					seq_y_char = seq_y[col-1]
				else:
					seq_y_char = '-'

				#If there's a match, the best option will always be to move diagonally
				if seq_y_char == seq_x_char:
					matrix[row][col] = matrix[row-1][col-1] + MATCH
				#Else, determine whether it's better overall to have a GAP, or to have a MISS
				else:
					if col != 0:
						current_max = max(current_max, matrix[row][col-1] + get_miss(in_gap))
					if row !=0 and col != 0:
						miss_max = matrix[row-1][col-1] + get_mismatch(seq_x_char, seq_y_char)
						current_max = max(current_max, miss_max)

					matrix[row][col] = current_max

				if current_max == miss_max and not in_gap:
					in_gap = True
				elif current_max != miss_max and in_gap:
					in_gap = False

	score = matrix[len(seq_x)][len(seq_y)]

	row = len(seq_x)
	col = len(seq_y)

	#Traverse backwards based on the maximum value, inserting the characters into an array
	aligned_seq_x = []
	gaps_left = len(seq_y) - len(seq_x)
	seq_x_char = seq_x[row-1]
	while col > 0:
		aligned_seq_x.append(seq_x_char)

		if row == 0:
			seq_x_char = '-'
			col -= 1
		else:
			max_val = max(matrix[row-1][col-1], matrix[row-1][col], matrix[row][col-1])

			if max_val == matrix[row][col-1] and gaps_left > 0:
				seq_x_char = '-'
				col -= 1
				gaps_left -=1
			else:
				seq_x_char = seq_x[row-2]
				row -= 1
				col -= 1

	#Reverse the strings that were entered backwards
	aligned_seq_x.reverse()

	#Convert from list of integers to string
	aligned_seq_x = ''.join(str(e) for e in aligned_seq_x)

	return aligned_seq_x


#Return transition miss if the gap is a transition, else return a transversion miss
def get_mismatch(seq_1_char, seq_2_char, PURINE=['A','G'], PYRIMIDINE=['C','T']):
	transition = (seq_1_char in PURINE and seq_2_char in PURINE) or (seq_1_char in PYRIMIDINE and seq_2_char in PYRIMIDINE)
	return TRANSITON_MISS if transition else TRANSVERSION_MISS

#Return extension penalty if the alignment is already in a gap, else return a new gap penalty
def get_miss(in_gap):
	return EXTENSION if in_gap else GAP 