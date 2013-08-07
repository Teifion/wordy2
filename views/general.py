from pyramid.renderers import get_renderer
from pyramid.httpexceptions import HTTPFound

from ..lib import (
    db,
)

from ..config import config

def menu(request):
    the_user = config['get_user_func'](request)
    layout = get_renderer(config['layout']).implementation()
    
    # We call but don't query this so that we can assign a profile
    # if none exists
    db.get_profile(the_user.id)
    
    game_list    = db.get_game_list(the_user.id, mode="Our turn")
    waiting_list = db.get_game_list(the_user.id, mode="Not our turn")
    
    return dict(
        title        = "Wordy",
        layout       = layout,
        the_user     = the_user,
        
        game_list    = list(game_list),
        waiting_list = list(waiting_list),
    )

def install(request):
    layout = get_renderer(config['layout']).implementation()
    
    if db.check_for_install():
        return HTTPFound(location=request.route_url("wordy.menu"))
    
    if "form.submitted" in request.params:
        f = request.params['wordlist'].file
        
        try:
            words = f.read().decode('latin-1')
        except Exception:
            words = f.read().decode('utf-8')
        
        db.install(words)
        
        # Register the achievements
        # achievement_functions.register(achievements.achievements)
        
        content = "Wordlist inserted correctly<br /><br /><a href='{route}' class='inbutton'>Wordy main menu</a>".format(
            route = request.route_url('wordy.menu')
        )
    else:
        content = """
        <form tal:condition="the_doc != None" action="{route}" method="post" accept-charset="utf-8" style="padding:10px;" enctype="multipart/form-data">
            
            <label for="wordlist">Wordlist file:</label>
            <input type="file" name="wordlist" size="40">
            <br />
            
            <input type="submit" name="form.submitted" />
        </form>
        """.format(
            route = request.route_url('wordy.install')
        )
    
    return dict(
        title   = "Wordy installation",
        layout  = layout,
        content = content,
    )

def stats(request):
    the_user = config['get_user_func'](request)
    db.get_profile(the_user.id)
    layout = get_renderer(config['layout']).implementation()
    
    stats = db.get_stats(the_user.id)
    
    return dict(
        title    = "Wordy stats",
        layout   = layout,
        the_user = the_user,
        
        stats    = stats,
    )

def head_to_head_stats(request):
    the_user = config['get_user_func'](request)
    message  = ""
    
    if "opponent_name" in request.params:
        opponent_name = request.params['opponent_name'].strip().upper()
        opponent = db.find_user(opponent_name)
        
    else:
        opponent_id = int(request.params['opponent_id'])
        opponent = db.find_user(opponent_id)
    
    stats = None
        
    if opponent is not None:
        stats = db.get_stats(the_user.id, opponent.id)
    else:
        message = "No opponent could be found"
    
    return dict(
        stats    = stats,
        message  = message,
        opponent = opponent,
    )

def preferences(request):
    the_user = config['get_user_func'](request)
    profile = db.get_profile(the_user.id)
    layout = get_renderer(config['layout']).implementation()
    message = ""
    
    if "form.submitted" in request.params:
        matchmaking = request.params['matchmaking']
        if matchmaking == "true":
            profile.matchmaking = True
        else:
            profile.matchmaking = False
        
        message = "Changes saved"
    
    return dict(
        title    = "Wordy preferences",
        layout   = layout,
        the_user = the_user,
        profile  = profile,
        message  = message,
    )
