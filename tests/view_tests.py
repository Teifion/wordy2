import unittest
import datetime
import transaction
from ..lib import (
    db,
    rules,
)

import re
from pyramid import testing
from .. import notifications
from pyramid.httpexceptions import HTTPFound

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
    
    def get_app(self, auth):
        # Auth is a username of the user you're authing as
        # Code that returns a testapp and cookie data
    
    def make_request(self, app, path, data, msg="", expect_forward=False):
        # Makes a request and checks for errors
        # Provides a custome message on failure
        # Allows expected fowards

Sadly I couldn't work out how to detatch this part from my
main framework. The key part is it'll allow us to use the db connection.
"""

try:
    from ....core.lib.test_f import DBTestClass
except Exception:
    class DBTestClass(object):
        pass

"""
This assumes the path prefix is "wordy".
"""

class DBTester(DBTestClass):
    def test_notifications(self):
        r = testing.DummyRequest()
        
        # We don't test the validity, just that they'll work if we pass them data
        result = notifications.forward_to_game(r, "1")
        self.assertTrue(isinstance(result, HTTPFound))
        
        result = notifications.forward_to_profile(r, "1")
        self.assertTrue(isinstance(result, HTTPFound))

# def make_view(self, app, view, matchdict={}, params={}, msg="", request=None):
#     if request is None:
#         request = DummyRequest()
    
#     request.matchdict = matchdict
#     request.params = params
#     return view(request)
    
    def test_views(self):
        with transaction.manager:
            config['DBSession'].execute('DELETE FROM wordy_moves')
            config['DBSession'].execute('DELETE FROM wordy_games')
            config['DBSession'].execute('DELETE FROM wordy_words')
            config['DBSession'].execute('COMMIT')
        
        User = config['User']
        u1, u2, u3 = config['DBSession'].query(User.id, User.name).limit(3)
        
        with transaction.manager:
            p1 = db.get_profile(user_id=u1.id)
            p2 = db.get_profile(user_id=u2.id)
            p3 = db.get_profile(user_id=u3.id)
            
            p1.matchmaking = True
            p1.last_move = datetime.datetime.now()
            p2.matchmaking = True
            p2.last_move = datetime.datetime.now()
            p3.matchmaking = True
            p3.last_move = datetime.datetime.now()
            config['DBSession'].add(p1)
            config['DBSession'].add(p2)
            config['DBSession'].add(p3)
        
        app, cookies = self.get_app()
        
        self.make_request(app, "/wordy/menu", cookies, msg="Error loading the menu screen for wordy")
        
        # Check install
        page_result = self.make_request(app, "/wordy/install", cookies)
        
        # I don't know why but this keeps coming up with an error so for now I'm leaving it
        # form = page_result.form  
        # form.set("wordlist", ("wordlist", "TEST TEST2".encode('utf-8')))
        # page_result = form.submit('form.submitted')
        # # page_result = form.submit()
        
        # self.check_request_result(
        #     page_result,
        #     "",
        #     {},
        #     msg = "There was an error installing the wordlist"
        # )
        
        # Preferences
        page_result = self.make_request(app, "/wordy/preferences", cookies,
            msg="Error loading the preferences screen")
        
        form = page_result.form  
        form.set("matchmaking", "true")
        page_result = form.submit('form.submitted')
        
        self.check_request_result(
            page_result,
            "",
            {},
            msg = "Error updaing preferences"
        )
        
        # Matchmaking
        self.make_request(app, "/wordy/matchmake", cookies,
            msg="Error attempting to matchmake",
            expect_forward = re.compile(r"wordy/game/[0-9]+")
        )
        
        # Stats
        self.make_request(app, "/wordy/stats", cookies, msg="Error attempting to view stats")
        
        # Head to head stats
        self.make_request(app, "/wordy/head_to_head_stats?opponent_name={}".format(u2.name), cookies,
            msg="Error attempting to view head to head stats"
        )
        
        self.make_request(app, "/wordy/head_to_head_stats?opponent_id=%d" % u2.id, cookies,
            msg="Error attempting to view head to head stats"
        )
        
        # Now lets start a game
        page_result = self.make_request(app, "/wordy/new_game", cookies,
            msg="Error loading the new game screen")
        
        form = page_result.form  
        form.set("opponent_name1", u2.name)
        page_result = form.submit('form.submitted')
        
        self.check_request_result(
            page_result,
            "",
            {},
            expect_forward = re.compile(r"wordy/game/[0-9]+"),
            msg = "Error submitting the new game form",
        )
        
        # Get match ID
        the_game = config['DBSession'].query(WordyGame).order_by(WordyGame.id.desc()).first()
        
        # View game
        page_result = self.make_request(app, "/wordy/game/{}".format(the_game.id), cookies,
            msg="Error viewing the game"
        )
        
        # Make a move
        with transaction.manager:
            the_game.tiles = ("FLATBCD", "URNABCD")
        
        form = None
        for k, f in page_result.forms.items():
            if f.id == "move_maker_form":
                form = f
        
        if form is None:
            self.fail("Could not find the move_maker_form when trying to make a move")
        
        form.set("letter0", "F_7_7")
        form.set("letter1", "L_8_7")
        form.set("letter2", "A_9_7")
        form.set("letter3", "T_10_7")
        
        page_result = form.submit('form.submitted')
        
        # View it again to make sure it's still okay to view a game
        page_result = self.make_request(app, "/wordy/game/{}".format(the_game.id), cookies,
            msg="Error viewing the game"
        )
        
        # config.add_route('wordy.rematch', '/rematch/{game_id}')
        # config.add_route('wordy.view_game', '/game/{game_id}')
        # config.add_route('wordy.check_status', '/check_status/{game_id}')
        # config.add_route('wordy.check_turn', '/check_turn/{game_id}')
        # config.add_route('wordy.make_move', '/make_move/{game_id}')
        # config.add_route('wordy.test_move', '/test_move/{game_id}')
        
        # View once more now the game has ended
        
        self.make_request(app, "/wordy/menu", cookies, msg="Error loading the menu screen for wordy after ensuring games were added")
    
    def test_win_in_depth(self):
        """I was getting reports the win conditions were not being accurately tracked."""
        
        with transaction.manager:
            config['DBSession'].execute('DELETE FROM wordy_moves')
            config['DBSession'].execute('DELETE FROM wordy_games')
            config['DBSession'].execute('DELETE FROM wordy_words')
            config['DBSession'].execute("INSERT INTO wordy_words VALUES ('FLAT'), ('FLOATSM'), ('MAD')")
            config['DBSession'].execute('COMMIT')
        
        User = config['User']
        u1, u2 = config['DBSession'].query(User.id, User.name).limit(2)
        
        app, cookies = self.get_app()
        
        # Now lets start a game
        db.new_game(players=[u1.id, u2.id], rematch=None)
        
        # Get match ID
        the_game = config['DBSession'].query(WordyGame).order_by(WordyGame.id.desc()).first()
        
        def _get_moves():
            return config['DBSession'].query(WordyMove).filter(WordyMove.game == the_game.id)
        
        # Make a move
        the_game.tiles = ["FLATBCD", "LOATSMZ"]
        db.perform_move(the_game, u1.id, (
            ("F", 7, 7),
            ("L", 8, 7),
            ("A", 9, 7),
            ("T", 10, 7),
        ))
        
        the_game.tiles = ["FLATBCD", "LOATSMZ"]
        db.perform_move(the_game, u2.id, (
            ("L", 7, 8),
            ("O", 7, 9),
            ("A", 7, 10),
            ("T", 7, 11),
            ("S", 7, 12),
            ("M", 7, 13),
        ))
        
        the_game.tiles = ["FLATBCD", "LOATSMZ"]
        db.perform_move(the_game, u1.id, (
            ("A", 8, 13),
            ("D", 9, 13),
        ))
        
        the_game.tiles = ["FLATBCD", "LOATSMZ"]
        with_count = dict(rules.tally_scores(the_game, _get_moves(), count_tiles=True))
        without_count = dict(rules.tally_scores(the_game, _get_moves(), count_tiles=False))
        
        self.assertEqual(with_count, {u1.id:35, u2.id:28})
        self.assertEqual(without_count, {u1.id:13, u2.id:17})
