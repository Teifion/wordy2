import unittest
import datetime
import transaction
from ..lib import (
    db,
)

from ..models import (
    WordyMove,
    WordyGame,
    WordyWord,
)

from ..config import config

"""
I've got a class defined in test_f which does the following.

class DBTestClass(unittest.TestCase):
    def setUp(self):
        self.session = _initTestingDB()
        self.config = routes(testing.setUp())
    
    def tearDown(self):
        DBSession.execute("ROLLBACK")
        self.session.remove()

Sadly I couldn't work out how to detatch this part from my
main framework. The key part is it'll allow us to use the db connection.
"""

try:
    from ....core.lib.test_f import DBTestClass
except Exception:
    class DBTestClass(object):
        pass

class DBTester(DBTestClass):
    def test_profiles(self):
        # Get a user to perform the test with
        User = config['User']
        u1, u2, u3 = [u[0] for u in config['DBSession'].query(User.id).limit(3)]
        
        # First delete the possible profile
        config['DBSession'].execute('DELETE FROM wordy_profiles')
        
        # Now try to add a new profile, we've deleted the existing profile
        # so it will need to create a new one anyway
        the_profile = db.get_profile(user_id=u1)
        
        # Now lets see what happens with matchmaking
        # it should fail because no other profiles have it
        r = db.find_match(the_profile)
        self.assertTrue(isinstance(r, str))
        
        # Lets add a new one then!
        p2 = db.get_profile(user_id=u2)
        p3 = db.get_profile(user_id=u3)
        
        # P2 needs some wins!
        p2.wins = 3
        p2.losses = 1
        config['DBSession'].add(p2)
        
        # Should still come back as false, we never enabled matchmaking
        r = db.find_match(the_profile)
        self.assertTrue(isinstance(r, str))
        
        p2.matchmaking = True
        p2.last_move = datetime.datetime.now()
        p3.matchmaking = True
        p3.last_move = datetime.datetime.now()
        config['DBSession'].add(p2)
        config['DBSession'].add(p3)
        
        r = db.find_match(the_profile)
        self.assertEqual(r, u3)
    
    def test_game_lists(self):
        def WG(**kwargs):
            return WordyGame(started=datetime.datetime.now(), **kwargs)
        
        # Find three users in the databse
        # if we don't have three users the test will fail
        User = config['User']
        u1, u2, u3 = [u[0] for u in config['DBSession'].query(User.id).limit(3)]
            
        # Delete all existing games
        config['DBSession'].execute('DELETE FROM wordy_moves')
        config['DBSession'].execute('DELETE FROM wordy_games')
        config['DBSession'].execute('DELETE FROM wordy_words')
        
        config['DBSession'].add(WG(current_player=u1, players=[u1,u2]))
        config['DBSession'].add(WG(current_player=u1, players=[u1,u2], winner=u1))
        config['DBSession'].add(WG(current_player=u2, players=[u1,u2]))
        config['DBSession'].add(WG(current_player=u2, players=[u1,u2], winner=u2))
        config['DBSession'].add(WG(current_player=u3, players=[u3,u2,u1]))
        config['DBSession'].add(WG(current_player=u3, players=[u3,u2]))
        
        config['DBSession'].add(WordyWord(word="FLAT"))
        config['DBSession'].add(WordyWord(word="TURN"))
        
        # db.get_game_list(user_id, mode="All")
        r = list(db.get_game_list(user_id=u1, mode="Ended"))
        self.assertEqual(len(r), 2)
        
        r = list(db.get_game_list(user_id=u1, mode="Our turn"))
        self.assertEqual(len(r), 1)
        
        r = list(db.get_game_list(user_id=u1, mode="Not our turn"))
        self.assertEqual(len(r), 2)
        
        self.assertRaises(KeyError, db.get_game_list, 
            user_id=u1,
            mode="Not a valid move"
        )
        
        # Now try making a new game
        game_id = db.new_game(players=[u1, u2], rematch=None)
        self.assertNotEqual(None, game_id)
        
        the_game = db.get_game(game_id=game_id)
        self.assertNotEqual(None, the_game)
        
        # Now for a game that doesn't exist
        self.assertRaises(ValueError, db.get_game,
            game_id=-1
        )
        
        the_game.tiles = ["FLATBCD", "URNABCD"]
        result = db.perform_move(the_game, u1, letters=[
            ['F', 7, 7],
            ['L', 8, 7],
            ['A', 9, 7],
            ['T', 10, 7],
        ])
        self.assertEqual(result, "success:")
        
        # Need to set it to a list so we don't try to alter
        # a tuple
        the_game.tiles = list(the_game.tiles)
        
        result = db.perform_move(the_game, u2, letters=[
            ['U', 10, 8],
            ['R', 10, 9],
            ['N', 10, 10],
        ])
        self.assertEqual(result, "success:")
        
        # Now we can try getting moves
        moves = list(db.get_moves(game_id))
        self.assertEqual(len(moves), 2)
        
        # Lets end it
        the_game.tiles = ["ABC", ""]
        self.assertEqual(the_game.winner, None)
        db.end_game(the_game)
        
        self.assertEqual(the_game.winner, u2)
        
        # Un-end it
        the_game.winner = None
        config['DBSession'].add(the_game)
        
        db.forfeit_game(the_game, user_id=u2)
        self.assertEqual(the_game.winner, u1)
        
        # Check these run without error
        db.completed_games(user_id=u1, opponent_id=None)
        db.completed_games(user_id=u1, opponent_id=u2)
        
        db.games_in_progress(user_id=u1, opponent_id=None)
        db.games_in_progress(user_id=u1, opponent_id=u2)
        
        db.games_won(user_id=u1, opponent_id=None)
        db.games_won(user_id=u1, opponent_id=u2)
        
        db.games_lost(user_id=u1, opponent_id=None)
        db.games_lost(user_id=u1, opponent_id=u2)
        
        db.games_drawn(user_id=u1, opponent_id=None)
        db.games_drawn(user_id=u1, opponent_id=u2)
        
        db.get_stats(user_id=u1, opponent_id=None)
        db.get_stats(user_id=u1, opponent_id=u2)
        
        # the_game.tiles = list(the_game.tiles)
        the_game.game_bag = str(the_game.game_bag)
        the_game.tiles = list(the_game.tiles)
        db.swap_letters(the_game, player_id=u1)
        
        the_game.game_bag = str(the_game.game_bag)
        the_game.tiles = list(the_game.tiles)
        db.swap_letters(the_game, player_id=u2)
        
        # Un-end it again so we can end it early!
        the_game.winner = None
        config['DBSession'].add(the_game)
        
        # First get the wrong player to end it
        self.assertRaises(KeyError, db.premature_end_game, the_game, u3)
        
        db.premature_end_game(the_game, u1)
        
        self.assertEqual(the_game.winner, u2)
    
    def test_install_funcs(self):
        config['DBSession'].execute('DELETE FROM wordy_words')
        
        # Check for lack of install
        r = db.check_for_install()
        self.assertEqual(r, False, msg="Wordy incorrectly assumes the game is installed")
        
        db.install("This is Installed")
        
        # Now it should all be hunky dory
        r = db.check_for_install()
        self.assertEqual(r, True, msg="Wordy incorrectly assumes the game is not installed, this may be a bug in the install function")
    
    def test_users(self):
        User = config['User']
        
        u1, u2, u3 = config['DBSession'].query(User.id, User.name).limit(3)
        
        names = db.get_names(players=[u1.id, u2.id, u3.id])
        self.assertEqual(names, {
            u1.id: u1.name,
            u2.id: u2.name,
            u3.id: u3.name,
        })
        
        found_id = db.find_user(identifier=u1.id)
        found_name = db.find_user(identifier=u1.id)
        
        self.assertEqual(found_id.id, found_name.id)
        self.assertEqual(found_id.name, found_name.name)
        
        self.assertEqual(found_id.id, u1.id)
        self.assertEqual(found_id.name, u1.name)
