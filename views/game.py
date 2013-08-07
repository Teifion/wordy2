import datetime
from pyramid.httpexceptions import HTTPFound

from pyramid.renderers import get_renderer

from ..lib import (
    db,
    rules,
)

from ..models import WordyMove

from ..config import config

def new_game(request):
    the_user = config['get_user_func'](request)
    layout = get_renderer(config['layout']).implementation()
    
    message = ""
    flash_colour = "A00"
    
    if "form.submitted" in request.params:
        opponents = list(filter(None, (
            request.params['opponent_name1'].strip().upper(),
            request.params['opponent_name2'].strip().upper(),
            request.params['opponent_name3'].strip().upper(),
        )))
        
        found_opponents = []
        found_names = []
        for uid, uname in config['DBSession'].query(config['User'].id, config['User'].name).filter(config['User'].name.in_(opponents)).limit(len(opponents)):
            found_opponents.append(uid)
            found_names.append(uname)
        
        if len(found_opponents) != len(opponents):
            message = """I'm sorry, we can't find all your opponents"""
        
        else:
            game_id = db.new_game([the_user.id] + found_opponents)
            return HTTPFound(location=request.route_url("wordy.view_game", game_id=game_id))
    
    return dict(
        title        = "Wordy",
        layout       = layout,
        the_user     = the_user,
        message      = message,
        flash_colour = flash_colour,
    )

def view_game(request):
    the_user = config['get_user_func'](request)
    layout = get_renderer(config['layout']).implementation()
    
    game_id = int(request.matchdict['game_id'])
    the_game = db.get_game(game_id)
    game_moves = list(db.get_moves(game_id))
    
    # Get our player number
    if the_user.id in the_game.players:
        player_number = the_game.players.index(the_user.id)
        letters = the_game.tiles[player_number]
    else:
        letters = ""
    
    the_board = rules.string_to_board(the_game.board.lower())
    scores = rules.tally_scores(the_game, game_moves, count_tiles=False)
    
    player_names = db.get_names(the_game.players)
    
    turn_log = []
    for m in game_moves:
        if m.score == 1:
            temp = "{} played {} for {} point"
        else:
            temp = "{} played {} for {} points"
        
        turn_log.append(temp.format(player_names[m.player], m.word.title(), m.score))
    
    last_move = WordyMove()
    last_move.timestamp = the_game.started
    if len(game_moves) > 0:
        last_move = game_moves[-1]
    
    return dict(
        title          = "Wordy",
        layout         = layout,
        the_board      = the_board,
        player_letters = list(letters.lower()),
        player_names = player_names,
        turn_log       = "<br />".join(turn_log),
        the_game       = the_game,
        last_move      = last_move,
        scores         = scores,
        now            = datetime.datetime.now(),
        spectator      = the_user.id in the_game.players,
        your_turn      = the_user.id == the_game.current_player and the_game.winner is None,
    )

def make_move(request):
    the_user = config['get_user_func'](request)
    game_id = int(request.matchdict['game_id'])
    the_game = db.get_game(game_id)
    
    # Special "moves"
    if "forfeit" in request.params:
        db.forfeit_game(the_game, the_user.id)
        return HTTPFound(location = request.route_url('wordy.game', game_id=the_game.id))
    
    if "end_game" in request.params:
        db.premature_end_game(the_game, the_user.id)
        return HTTPFound(location = request.route_url('wordy.game', game_id=the_game.id))
    
    if "swap" in request.params:
        db.swap_letters(the_game, the_user.id)
        return HTTPFound(location = request.route_url('wordy.game', game_id=the_game.id))
    
    if "pass" in request.params:
        db.pass_turn(the_game, the_user.id)
        return HTTPFound(location = request.route_url('wordy.game', game_id=the_game.id))
    
    player_number = the_game.players.index(the_user.id)
    player_letters = the_game.tiles[player_number]
    new_letters = []
    
    for k, tile_info in request.params.items():
        if tile_info != "":
            l, x, y = tile_info.split("_")
            
            try:
                new_letters.append((player_letters[int(l)], int(x), int(y)))
            except Exception:
                # I have a hunch this is caused by submitting the move twice in a row
                return "failure:List index exception. I can't work out why this is happening or if you even see anything. If you do see this, please let Teifion know."
    
    if new_letters == []:
        return "failure:You didn't make a move"
    
    print("\n\n")
    print(new_letters)
    print("\n\n")
    return "failure:test"
    
    request.do_not_log = True
    return db.perform_move(the_game, request.user.id, new_letters)

def rematch(request):
    the_user = config['get_user_func'](request)
    game_id  = int(request.matchdict['game_id'])
    the_game = db.get_game(game_id)
    
    # Not a player? Send them back to the menu
    if the_user.id != the_game.player1 and the_user.id != the_game.player2:
        return HTTPFound(location=request.route_url("wordy.menu"))
    
    # Not over yet? Send them back to the game in question.
    if the_game.winner == None:
        return HTTPFound(location=request.route_url("wordy.view_game", game_id=game_id))
    
    if the_user.id == the_game.player1:
        opponent = db.find_user(the_game.player2)
    else:
        opponent = db.find_user(the_game.player1)
    
    newgame_id = db.new_game(the_user, opponent, rematch=game_id)
    the_game.rematch = newgame_id
    return HTTPFound(location=request.route_url("wordy.view_game", game_id=newgame_id))

def check_turn(request):
    request.do_not_log = True
    
    the_user = config['get_user_func'](request)
    game_id  = int(request.matchdict['game_id'])
    
    the_game = db.get_game(game_id)
    if rules.current_player(the_game) == the_user.id:
        return "True"
    return "False"
