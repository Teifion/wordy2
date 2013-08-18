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
        uid = config['DBSession'].query(User.id).first()[0]
        
        # First delete the possible profile
        config['DBSession'].execute('DELETE FROM wordy_profiles')
        
        # Now try to add a new profile, we've deleted the existing profile
        # so it will need to create a new one anyway
        db.get_profile(user_id=uid)
    
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
        self.assertEqual(the_game.winner, None)
        db.end_game(the_game)
        
        self.assertEqual(the_game.winner, u1)
        
        # db.completed_games(user_id, opponent_id=None)
        # db.games_in_progress(user_id, opponent_id=None)
        # db.games_won(user_id, opponent_id=None)
        # db.games_lost(user_id, opponent_id=None)
        # db.games_drawn(user_id, opponent_id=None)
        # db.get_stats(user_id, opponent_id=None)
        # db.check_for_install()
        # db.install(words)
        # db.find_match(profile)
        # db.forfeit_game(the_game, user_id)
        # db.premature_end_game(the_game, user_id)
    
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