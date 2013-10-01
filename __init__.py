def wordy_nimblescan():
    try:
        from ...nimblescan import api
    except ImportError:
        try:
            from ..nimblescan import api
        except ImportError:
            return
    
    api.register('wordy.menu', "Wordy - Menu", ['games'], (lambda r: True), api.make_forwarder("wordy.menu"))
    api.register('wordy.new_game', "Wordy - New game", ['games'], (lambda r: True), api.make_form_forwarder("wordy.new_game", []), '<label for="ns_opponent">Opponent:</label> <input type="text" name="opponent_name1" id="ns_opponent" value="" style="display:inline-block;"/>')
    api.register('wordy.stats', "Wordy - Stats", ['games'], (lambda r: True), api.make_forwarder("wordy.stats"))
    api.register('wordy.preferences', "Wordy - Preferences", ['games'], (lambda r: True), api.make_forwarder("wordy.preferences"))

def wordy_notifications():
    try:
        from ...communique import register, send
    except ImportError:
        try:
            from ..communique import register, send
        except ImportError:
            return
    
    from .notifications import forward_to_game, forward_to_profile
    
    register('wordy.new_move', 'New move', 'http://localhost:6543/static/images/communique/wordy.png', forward_to_game)
    register('wordy.end_game', 'Game over', 'http://localhost:6543/static/images/communique/wordy.png', forward_to_game)
    register('wordy.win_game', 'Victory!', 'http://localhost:6543/static/images/communique/wordy.png', forward_to_game)

def includeme(config):
    from . import views
    
    config.add_route('wordy.install', '/install')
    config.add_view(views.install, route_name='wordy.install', renderer='templates/general/install.pt', permission='loggedin')
    
    # General views
    config.add_route('wordy.menu', '/menu')
    config.add_route('wordy.stats', '/stats')
    config.add_route('wordy.head_to_head_stats', '/head_to_head_stats')
    config.add_route('wordy.preferences', '/preferences')
    
    config.add_view(views.menu, route_name='wordy.menu', renderer='templates/general/menu.pt', permission='loggedin')
    config.add_view(views.stats, route_name='wordy.stats', renderer='templates/general/stats.pt', permission='loggedin')
    config.add_view(views.preferences, route_name='wordy.preferences', renderer='templates/general/preferences.pt', permission='loggedin')
    config.add_view(views.head_to_head_stats, route_name='wordy.head_to_head_stats', renderer='templates/general/head_to_head_stats.pt', permission='loggedin')
    
    # Game views
    config.add_route('wordy.new_game', '/new_game')
    config.add_route('wordy.rematch', '/rematch/{game_id}')
    
    config.add_route('wordy.view_game', '/game/{game_id}')
    config.add_route('wordy.check_status', '/check_status/{game_id}')
    config.add_route('wordy.check_turn', '/check_turn/{game_id}')
    config.add_route('wordy.make_move', '/make_move/{game_id}')
    config.add_route('wordy.test_move', '/test_move/{game_id}')
    config.add_route('wordy.matchmake', '/matchmake')
    
    config.add_route('wordy.recalculate', '/recalculate')
    
    config.add_view(views.new_game, route_name='wordy.new_game', renderer='templates/game/new_game.pt', permission='loggedin')
    config.add_view(views.matchmake, route_name='wordy.matchmake', renderer='templates/general/matchmake.pt', permission='loggedin')
    config.add_view(views.view_game, route_name='wordy.view_game', renderer='templates/game/view_game.pt', permission='loggedin')
    
    config.add_view(views.make_move, route_name='wordy.make_move', renderer='string', permission='loggedin')
    config.add_view(views.rematch, route_name='wordy.rematch', renderer='string', permission='loggedin')
    config.add_view(views.check_turn, route_name='wordy.check_turn', renderer='string', permission='loggedin')
    config.add_view(views.check_status, route_name='wordy.check_status', renderer='string', permission='loggedin')
    
    config.add_view(views.recalculate, route_name='wordy.recalculate', permission='loggedin')
    
    wordy_notifications()
    wordy_nimblescan()
    
    return config
