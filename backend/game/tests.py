clues = ['Clue 1 Kobe Bryant', 'Clue 1 Kobe Bryant']
word_to_guess = 'Kobe Bryant'
checked_clues = []
for clue in clues:
    checked_clues.append(clue.replace(word_to_guess, ''.join(['X' for letter in word_to_guess])))
print(clues[0].replace(word_to_guess, ''.join(['X' for letter in word_to_guess])))
