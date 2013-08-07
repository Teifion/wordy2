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
        empty_game = WordyGame(
            players        = [1,2],
            tiles          = ["DIRTABC", "ABCDEF"],
            current_player = 1,
            board          = " "*255
        )
        
        # Playing "Dirt" horrizontally from the centre tile
        # This should be a successful move
        letters = [('R', 9, 7), ('T', 10, 7), ('I', 8, 7), ('D', 7, 7)]
        scores, new_board = rules.test_move(empty_game, player_id=1, letters=letters, db_words=("DIRT",))
        self.assertEqual(scores[0], ("DIRT", 5))
    
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
