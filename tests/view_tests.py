import unittest
import datetime
import transaction
from ..lib import (
    db,
)

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
        u1, u2 = [u[0] for u in config['DBSession'].query(User.name).limit(2)]
        
        app, cookies = self.get_app()
        
        self.make_request(app, "/wordy/menu", cookies, msg="Error loading the menu screen for wordy")
        
        # Check install
        self.make_request(app, "/wordy/install", cookies)
        
        # Now try performing the install
        
        
        # config.add_route('wordy.preferences', '/preferences')
        # config.add_route('wordy.new_game', '/new_game')
        # config.add_route('wordy.rematch', '/rematch/{game_id}')
        # config.add_route('wordy.view_game', '/game/{game_id}')
        # config.add_route('wordy.check_status', '/check_status/{game_id}')
        # config.add_route('wordy.check_turn', '/check_turn/{game_id}')
        # config.add_route('wordy.make_move', '/make_move/{game_id}')
        # config.add_route('wordy.test_move', '/test_move/{game_id}')
        # config.add_route('wordy.matchmake', '/matchmake')
        
        # config.add_route('wordy.stats', '/stats')
        # config.add_route('wordy.head_to_head_stats', '/head_to_head_stats')
        
        
        self.make_request(app, "/wordy/menu", cookies, msg="Error loading the menu screen for wordy after ensuring games were added")
