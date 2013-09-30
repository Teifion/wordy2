import math

import random
import datetime
from collections import defaultdict

from ..config import config

from ..models import (
    WordyWord,
)

# http://en.wikipedia.org/w/index.php?title=File:Blank_Scrabble_board_with_coordinates.svg&page=1
# Double/Triple word scores
dws = (
    (1,1),              (13,1),
      (2,2),          (12,2),
        (3,3),      (11,3),
          (4,4),  (10,4),
        
          (4,10), (10,10),
        (3,11),     (11,11),
      (2,12),         (12,12),
    (1,13),             (13,13),
)
tws = (
    (0,0),  (7,0),  (14,0),
    (0,7),          (14,7),
    (0,14), (7,14), (14,14)
)

# Double/Triple letter scores
dls = (
          (3,0),                  (11,0),
                  (6,2),  (8,2),
    (0,3),            (7,3),              (14,3),
    
        (2,6),    (6,6),  (8,6),    (12,6),
          (3,7),                  (11,7),
        (2,8),    (6,8),  (8,8),    (12,8),
        
    (0,11),           (7,11),             (14,11),
                  (6,12), (8,12),
          (3,14),                  (11,14),
)
tls = (
            (5,1),      (9,1),
    
    (1,5),  (5,5),      (9,5),   (13,5),
    
    (1,9),  (5,9),      (9,9),   (13,9),
    
            (5,13),     (9,13),
)

# ABCDEFGHIJKLMNO
# 0123456789ABCDE

default_bag = "EEEEEEEEEEEEAAAAAAAAAIIIIIIIIIOOOOOOOONNNNNNRRRRRRTTTTTTLLLLSSSSUUUUDDDDGGGBBCCMMPPFFHHVVWWYYKJXQZ**"
default_bag = "EEEEEEEEEEEEAAAAAAAAAIIIIIIIIIOOOOOOOONNNNNNRRRRRRTTTTTTLLLLSSSSUUUUDDDDGGGBBCCMMPPFFHHVVWWYYKJXQZ"

testing_board = """
ABCDEFGHIJKLMNO
PQRSTUVWXYZ____
_______________
_______________
_______________
_______________
_______________
_______________
_______________
_______________
_______________
_______________
_______________
_______________
_______________
""".replace("\n","").replace("_"," ")

# For easy copy+paste into DB
"ABCDEFGHIJKLMNOPQRSTUVWXYZ                                                                                                                                                                                                       "
dummy_board = """
___Q___G_______
___U_P_A_______
CEDI_A_I_______
___NORITE______
_____L____Y____
____BEAU_DOS__Y
____O_____G___O
A___T_SIZIER__R
V__WHEW___E_ORE
A__I_MU_____N__
SHUN__MIGRATE__
T__E___V_____B_
_____DJINN___U_
_______E_O___L_
____FOPS_D_TALC
""".replace("\n","").replace("_"," ")

# For easy copy+paste into DB
"   Q   G          U P A       CEDI A I          NORITE           L    Y        BEAU DOS  Y    O     G   OA   T SIZIER  RV  WHEW   E OREA  I MU     N  SHUN  MIGRATE  T  E   V     B      DJINN   U        E O   L     FOPS D TALC"

# http://en.wikipedia.org/wiki/Scrabble_letter_distributions
# 2 blank tiles (scoring 0 points)
# 1 point: E ×12, A ×9, I ×9, O ×8, N ×6, R ×6, T ×6, L ×4, S ×4, U ×4
# 2 points: D ×4, G ×3
# 3 points: B ×2, C ×2, M ×2, P ×2
# 4 points: F ×2, H ×2, V ×2, W ×2, Y ×2
# 5 points: K ×1
# 8 points: J ×1, X ×1
# 10 points: Q ×1, Z ×1

letter_values = {
    "A": 1,
    "B": 3,
    "C": 3,
    "D": 2,
    "E": 1,
    "F": 4,
    "G": 2,
    "H": 4,
    "I": 1,
    "J": 8,
    "K": 5,
    "L": 1,
    "M": 3,
    "N": 1,
    "O": 1,
    "P": 3,
    "Q": 10,
    "R": 1,
    "S": 1,
    "T": 1,
    "U": 1,
    "V": 4,
    "W": 4,
    "X": 8,
    "Y": 4,
    "Z": 10,
    "*": 0,
    " ": 0,
    "_": 0,
}

vowels = "AEIOU"

def pick_from_bag(the_bag, tiles=7, attempt=7, existing_tiles=""):
    if type(the_bag) == str:
        new_bag = list(the_bag)
    
    letters = []
    
    while len(letters) < tiles and len(new_bag) > 0:
        r = random.randint(0, len(new_bag)-1)
        letters.append(new_bag.pop(r))
    
    # Try to never have too many or too few vowels if we can help it
    # technically this is not part of the core scrabble rules
    total_new_tiles = existing_tiles + "".join(letters)
    vowel_count = 0
    for v in vowels:
        vowel_count += total_new_tiles.count(v)
    
    if vowel_count < 2 or vowel_count > 5:
        if attempt > 1:
            return pick_from_bag(the_bag, tiles=tiles, attempt=attempt-1)
    
    return "".join(letters), "".join(new_bag)

def string_to_board(board_string):
    the_board = []
    
    for r in range(15):
        a = r * 15
        b = r * 15 + 15
        the_board.append(list(board_string[a:b]))
    
    return the_board

def board_to_string(board_lists):
    return "".join(["".join(b) for b in board_lists])

def tally_scores(the_game, moves, count_tiles=False):
    results = defaultdict(int)
    
    for t in moves:
        results[t.player] += t.score
    
    # Add in remaining tiles, these will be under the player numbers
    if count_tiles:
        for i, p in enumerate(the_game.players):
            temp = 0
            for j, p2 in enumerate(the_game.players):
                if j == i: continue
                temp += sum([letter_values[l] for l in the_game.tiles[j]])
            
            results[p] += temp
    
    return results

def test_move(the_game, player_id, letters, db_words=None):
    """
    You can pass the words to the function to save it making a databse call.
    This is designed to make it easier to test.
    """
    
    if player_id != the_game.current_player:
        return "It is not your turn"
    
    # Whose turn is it anyways?
    pnum = the_game.players.index(player_id)
    player_letters = the_game.tiles[pnum]
    
    # Get the board as a string
    b = string_to_board(the_game.board)
    
    # We want to make sure all the letters can be placed in these locations
    xs, ys = set(), set()
    for l, x, y in letters:
        if x < 0 or x > 14 or y < 0 or y > 14:
            return "{},{} is not a valid tile (15x15 board size)".format(x, y)
        
        if b[y][x] != " ":
            return "{},{} is already occupied by a letter".format(x, y)
        
        xs.add(x)
        ys.add(y)
    
    if len(xs) > 1 and len(ys) > 1:
        return "You must place all your tiles in one row or one column"
        
    # Now make sure they're placing the tiles next to existing tiles
    # At least one tiles needs to be non-diagonally next to another
    is_next_to_a_tile = False
    
    for l, x, y in letters:
        if is_next_to_a_tile: continue
        
        # X
        if x > 0 and b[y][x-1] != " ": is_next_to_a_tile = True
        if x < 14 and b[y][x+1] != " ": is_next_to_a_tile = True
        
        # Y
        if y > 0 and b[y-1][x] != " ": is_next_to_a_tile = True
        if y < 14 and b[y+1][x] != " ": is_next_to_a_tile = True
    
    if not is_next_to_a_tile and the_game.board != " "*255:
        return "You must place your tiles next to existing tiles"
    
    # Add letters to the board
    for l, x, y in letters:
        b[y][x] = l
    
    # Next we want to make sure there are no gaps between our tiles
    if len(xs) > 1:
        minx, maxx = min(xs), max(xs)
        y = list(ys)[0]
        
        for x in range(minx, maxx):
            if b[y][x] == " ":
                return "Your tiles must all be part of the same word (no gaps allowed)"
        
    if len(ys) > 1:
        miny, maxy = min(ys), max(ys)
        x = list(xs)[0]
        
        for y in range(miny, maxy):
            if b[y][x] == " ":
                return "Your tiles must all be part of the same word (no gaps allowed)"
    
    # If it's turn 0 then we need to make sure the centre is covered
    if b[7][7] == " ":
        return "The centre tile is not covered"
    
    # Now we want to find all the words to check in the datbase
    words = []
    covered = set()
    for l, x, y in letters:
        if (x,y) in covered: continue
        
        # Go left until we hit an empty space or edge of the board
        temp_x = x
        temp_l = l
        while temp_x >= 0 and temp_l != " ":
            temp_l = b[y][temp_x]
            temp_x -= 1
        
        temp_x += 1
        if temp_l == " ": temp_x += 1
        temp_l = ""
        
        # Read right until the same, this is one word
        new_word = []
        word_points = 0
        word_multiplier = 1
        while temp_x <= 14 and temp_l != " ":
            covered.add((temp_x, y))
            temp_l = b[y][temp_x]
            new_word.append(temp_l)
           
            letter_multiplier = 1
           
            # If it's fresh we check for special tiles
            if (temp_l, temp_x, y) in letters:
                if (temp_x, y) in dws: word_multiplier *= 2
                if (temp_x, y) in tws: word_multiplier *= 3
               
                if (temp_x, y) in dls: letter_multiplier = 2
                if (temp_x, y) in tls: letter_multiplier = 3
           
            word_points += (letter_values[temp_l] * letter_multiplier)
            temp_x += 1
        
        new_word = "".join(new_word).strip()
        if len(new_word) > 1:
            words.append((new_word, word_points * word_multiplier))
    
    # Repeat for Y
    # We don't put them in the same loop as it's not easy to track which tiles we've already covered
    covered = set()
    for l, x, y in letters:
        if (x,y) in covered: continue
        
        # Go left until we hit an empty space or edge of the board
        temp_y = y
        temp_l = l
        while temp_y >= 0 and temp_l != " ":
            temp_l = b[temp_y][x]
            temp_y -= 1
        
        temp_y += 1
        if temp_l == " ": temp_y += 1
        temp_l = ""
        
        # Read right until the same, this is one word
        new_word = []
        word_points = 0
        word_multiplier = 1
        while temp_y <= 14 and temp_l != " ":
            covered.add((x, temp_y))
            temp_l = b[temp_y][x]
            new_word.append(temp_l)
           
            letter_multiplier = 1
           
            # If it's fresh we check for special tiles
            if (temp_l, x, temp_y) in letters:
                if (x, temp_y) in dws: word_multiplier *= 2
                if (x, temp_y) in tws: word_multiplier *= 3
               
                if (x, temp_y) in dls: letter_multiplier = 2
                if (x, temp_y) in tls: letter_multiplier = 3
           
            word_points += (letter_values[temp_l] * letter_multiplier)
            temp_y += 1
        
        new_word = "".join(new_word).strip()
        if len(new_word) > 1:
            words.append((new_word, word_points * word_multiplier))
    
    # Get a list of these words from the database
    # any word not in the list we get back is an invalid word
    if db_words is None:
        db_words = get_words_from_db([w[0] for w in words])
    
    invalid = []
    for w, s in words:
        if w not in db_words:
            invalid.append(w.title())
    
    if invalid != []:
        if len(invalid) == 1:
            return "{} is not a valid word".format(invalid[0])
        else:
            return "{} and {} are not valid words".format(", ".join(invalid[:-1]), invalid[-1])
    
    if len(letters) == 7:
        words.append(("Used 7 tiles at once", 50))
    
    return words, b

# Technically this should go in db as it's not a pure (ish) function
# however that'd be a circular import and it's not modifying the data
# so I'm going to leave it here
def get_words_from_db(words):
    return [w[0] for w in config['DBSession'].query(WordyWord.word).filter(WordyWord.word.in_(words)).limit(len(words))]

def scan_for_end(the_game):
    if the_game.game_bag == "":
        if "" in the_game.tiles:
            return True
    return False

def win_ratio(wins, total_games, decimal_points=2):
    if total_games < 1: return 0
    if wins < 1: return 0
    if wins > total_games:
        raise ValueError("Cannot have more wins than total games")
    return round(100 * (wins / total_games), decimal_points)
