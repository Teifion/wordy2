import unittest
from ..lib import (
    rules,
)

from ..models import (
    WordyMove,
    WordyGame,
)

class RulesTester(unittest.TestCase):
    def test_counts(self):
        board_size = 15*15
        
        self.assertEqual(len(rules.testing_board), board_size)
        self.assertEqual(len(rules.dummy_board), board_size)
        
        # 26 letters and 3 special tiles
        self.assertEqual(len(rules.letter_values), 26+3)
        self.assertEqual(len(rules.vowels), 5)
    
    def test_pick_from_bag(self):
        for n in range(1,8):
            tiles, new_bag = rules.pick_from_bag(rules.default_bag, tiles=n, attempt=7, existing_tiles="")
            
            self.assertEqual(len(tiles), n)
            self.assertEqual(len(new_bag), len(rules.default_bag) - n)
    
    def test_board_converters(self):
        list_ver = rules.string_to_board(rules.dummy_board)
        string_ver = rules.board_to_string(list_ver)
        
        self.assertNotEqual(list_ver, string_ver)
        self.assertEqual(string_ver, rules.dummy_board)
    
    def test_tally_moves(self):
        moves = (
            WordyMove(game=1, player=1, word="One", score=1),
            WordyMove(game=1, player=2, word="Two", score=2),
            WordyMove(game=1, player=1, word="Three", score=3),
            WordyMove(game=1, player=2, word="Four", score=4),
        )
        
        the_game = WordyGame(
            players=[1,2],
            tiles=["AA", "ZZ"],
        )
        
        scores = rules.tally_scores(the_game, moves, count_tiles=False)
        self.assertEqual(scores[1], 4)
        self.assertEqual(scores[2], 6)
        
        scores = rules.tally_scores(the_game, moves, count_tiles=True)
        self.assertEqual(scores[1], 20)
        self.assertEqual(scores[2], 2)
    
    def test_move(self):
        # This test case first checks a successful move will work, then ensures
        # that every form of failure is correctly picked up
        
        def parts(board=" "*255):
            return WordyGame(
            players        = [1,2],
            tiles          = ["DIRTABC", "ABCDEF"],
            current_player = 1,
            board          = board,
        ), [['R', 9, 7], ['T', 10, 7], ['I', 8, 7], ['D', 7, 7]]
        
        
        # Playing "Dirt" horrizontally from the centre tile
        # This should be a successful move
        the_game, letters = parts()
        scores, new_board = rules.test_move(the_game, player_id=1, letters=letters, db_words=("DIRT",))
        self.assertEqual(scores[0], ("DIRT", 5))
        self.assertEqual(len(scores), 1)
        
        # Test 7 tile score
        the_game, letters = parts()
        letters = [['R', 9, 7], ['T', 10, 7], ['I', 8, 7], ['D', 7, 7], ['A', 11, 7], ['A', 12, 7], ['A', 13, 7]]
        scores, new_board = rules.test_move(the_game, player_id=1, letters=letters, db_words=("DIRTAAA",))
        self.assertEqual(scores[0], ("DIRTAAA", 8))
        self.assertEqual(scores[1], ("Used 7 tiles at once", 50))
        self.assertEqual(len(scores), 2)
        
        # Now we're going to test for some excepcted failures
        # Not your turn
        the_game, letters = parts()
        the_game.current_player = 2
        result = rules.test_move(the_game, player_id=1, letters=letters)
        self.assertEqual(result, "It is not your turn")
        
        # Out of bounds
        for x in (-1, 15):
            for y in (-1, 15):
                the_game, letters = parts()
                letters = [['A', x, y]]
                result = rules.test_move(the_game, player_id=1, letters=letters)
                self.assertEqual(result, "{},{} is not a valid tile (15x15 board size)".format(x, y))
        
        # Tile already taken
        the_game, letters = parts("A" + " "*255)
        letters = [['A', 0, 0]]
        result = rules.test_move(the_game, player_id=1, letters=letters)
        self.assertEqual(result, "0,0 is already occupied by a letter")
        
        # All on same row/column
        the_game, letters = parts()
        letters = [['A', 0, 0], ['A', 1, 1]]
        result = rules.test_move(the_game, player_id=1, letters=letters)
        self.assertEqual(result, "You must place all your tiles in one row or one column")
        
        # Next to existing tiles
        the_game, letters = parts("A" + " "*255)
        letters = [['A', 3, 0], ['A', 4, 0]]
        result = rules.test_move(the_game, player_id=1, letters=letters)
        self.assertEqual(result, "You must place your tiles next to existing tiles")
        
        # No gaps (X)
        the_game, letters = parts("A   A" + " "*255)
        letters = [['A', 1, 0], ['A', 3, 0]]
        result = rules.test_move(the_game, player_id=1, letters=letters)
        self.assertEqual(result, "Your tiles must all be part of the same word (no gaps allowed)")
        
        # No gaps (Y), takes a bit more to add the empty rows
        board = [" "]*255
        board[0] = "A"
        board[5*15] = "A"
        the_game, letters = parts("".join(board))
        letters = [['A', 0, 1], ['A', 0, 3]]
        result = rules.test_move(the_game, player_id=1, letters=letters)
        self.assertEqual(result, "Your tiles must all be part of the same word (no gaps allowed)")
        
        # Centre tile must be covered
        the_game, letters = parts("A" + " "*255)
        letters = [['A', 1, 0], ['A', 2, 0]]
        result = rules.test_move(the_game, player_id=1, letters=letters)
        self.assertEqual(result, "The centre tile is not covered")
        
        # To ensure it's correctly reading the words, we 
        # don't send it a valid list of words so it
        # assumes all are invalid
        # First, check X
        the_game, letters = parts()
        result = rules.test_move(the_game, player_id=1, letters=letters, db_words=[])
        self.assertEqual(result, "Dirt is not a valid word")
        
        # Now check Y
        the_game, letters = parts()
        letters = [('B', 7, 9), ('A', 7, 10), ('C', 7, 8), ('D', 7, 7)]
        result = rules.test_move(the_game, player_id=1, letters=letters, db_words=[])
        self.assertEqual(result, "Dcba is not a valid word")
        
        # Now check both
        the_game, letters = parts(rules.dummy_board)
        letters = [('R', 2, 1)]
        result = rules.test_move(the_game, player_id=1, letters=letters, db_words=[])
        self.assertEqual(result, "Ru and Rd are not valid words")
        
        # More than a 2x2 area
        the_game, letters = parts(rules.dummy_board)
        letters = [('R', 2, 1), ('T', 1, 1)]
        result = rules.test_move(the_game, player_id=1, letters=letters, db_words=[])
        self.assertEqual(result, "Tru, Rd and Te are not valid words")
        
        # Check it matches the words correctly
        the_game, letters = parts()
        result = rules.test_move(the_game, player_id=1, letters=letters, db_words=("DIRTT", "DIR"))
        self.assertEqual(result, "Dirt is not a valid word")
    
    def test_scan_for_end(self):
        def game():
            return WordyGame(
                players        = [1,2],
                tiles          = ["DIRTABC", "ABCDEF"],
                game_bag       = "ABC",
            )
        
        # Test to make sure default doesn't end
        default_game = game()
        self.assertEqual(rules.scan_for_end(default_game), False)
        
        # Empty bag but not tiles
        empty_bag = game()
        empty_bag.game_bag = ""
        self.assertEqual(rules.scan_for_end(empty_bag), False)
        
        # One set of empty tiles
        empty_tiles = game()
        empty_tiles.game_bag = ""
        empty_tiles.tiles[0] = ""
        self.assertEqual(rules.scan_for_end(empty_tiles), True)
    
    def test_win_ratio(self):
        # Test outliers
        r = rules.win_ratio(wins=0, total_games=0, decimal_points=2)
        self.assertEqual(r, 0)
        
        r = rules.win_ratio(wins=1, total_games=-1, decimal_points=2)
        self.assertEqual(r, 0)
        
        r = rules.win_ratio(wins=-1, total_games=1, decimal_points=2)
        self.assertEqual(r, 0)
        
        r = rules.win_ratio(wins=-1, total_games=-1, decimal_points=2)
        self.assertEqual(r, 0)
        
        # Exception
        self.assertRaises(ValueError, rules.win_ratio, wins=3, total_games=2, decimal_points=2)
        
        # Standard behaviour
        r = rules.win_ratio(wins=1, total_games=2, decimal_points=2)
        self.assertEqual(r, 50)
        
        r = rules.win_ratio(wins=0, total_games=2, decimal_points=2)
        self.assertEqual(r, 0)
        
        r = rules.win_ratio(wins=2, total_games=2, decimal_points=2)
        self.assertEqual(r, 100)
