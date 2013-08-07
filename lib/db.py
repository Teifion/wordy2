"""
These functions handle talking to the database and should be considered
impure.
"""

from ..config import config

from ..models import (
    WordyGame,
    WordyMove,
    WordyProfile,
)

from sqlalchemy import or_, and_
from sqlalchemy import func
import datetime

from . import (
    rules,
)

def get_profile(user_id):
    the_profile = config['DBSession'].query(WordyProfile).filter(WordyProfile.user == user_id).first()
    
    if the_profile is None:
        the_profile = add_empty_profile(user_id)
    
    return the_profile

def add_empty_profile(user_id):
    the_profile = WordyProfile()
    the_profile.user = user_id
    
    config['DBSession'].add(the_profile)
    return the_profile

def get_game_list(user_id, mode):
    """Games waiting for us to make our move."""
    User = config['User']
    
    filters = [
        # user_id == func.any(WordyGame.players),
        "{:d} = ANY(wordy_games.players)".format(user_id),
        User.id == WordyGame.current_player,
    ]
    
    if mode == "All":
        raise Exception("Not implemented")
    
    elif mode == "Ended":
        filters.append(WordyGame.winner != None)
        
    elif mode == "Our turn":
        filters.append(WordyGame.current_player == user_id)
        filters.append(WordyGame.winner == None)
        
    elif mode == "Not our turn":
        filters.append(WordyGame.current_player != user_id)
        filters.append(WordyGame.winner == None)
    
    else:
        raise KeyError("No handler for mode of '{}'".format(mode))
    
    return config['DBSession'].query(WordyGame.id, User.name, WordyGame.turn).filter(*filters)

def find_user(identifier):
    User = config['User']
    
    if type(identifier) == str:
        found = config['DBSession'].query(User.id).filter(User.name == identifier).first()
        if found == None:
            return None
        return config['get_user']({'id':found[0], 'name':identifier})
    
    elif type(identifier) == int:
        found = config['DBSession'].query(User.name).filter(User.id == identifier).first()
        if found == None:
            return None
        return config['get_user']({'id':identifier, 'name':found[0]})
    
    else:
        raise KeyError("No handler for identifier type of '{}'".format(type(identifier)))

def new_game(players, rematch=None):
    # Setup the initial tiles
    game         = WordyGame()
    the_bag      = rules.default_bag
    game.players = players
    game.tiles   = []
    
    for p in game.players:
        new_tiles, the_bag = rules.pick_from_bag(the_bag, tiles=7)
        game.tiles.append(new_tiles)
    
    game.game_bag       = str(the_bag)
    game.turn           = 0
    game.current_player = players[0]
    game.started        = datetime.datetime.now()
    game.source         = rematch
    
    config['DBSession'].add(game)
    
    # Get game ID
    game_id = config['DBSession'].query(WordyGame.id).filter(
        WordyGame.current_player == players[0],
        WordyGame.source == rematch,
    ).order_by(WordyGame.id.desc()).first()[0]
    
    return game_id

def get_game(game_id):
    the_game = config['DBSession'].query(WordyGame).filter(WordyGame.id == game_id).first()
    
    if the_game == None:
        raise ValueError("We were unable to find the game")
    
    return the_game
    
def get_moves(game_id):
    return config['DBSession'].query(WordyMove).filter(WordyMove.game == game_id).order_by(WordyMove.timestamp.asc())

def perform_move(the_game, player_id, letters):
    result = rules.test_move(the_game, player_id, letters)
    
    if isinstance(result, str):
        return result
    else:
        words, new_board = result
    
    pnum = the_game.players.index(player_id)
    player_letters = the_game.tiles[pnum]
    
    for l, x, y in letters:
        player_letters = player_letters.replace(l, "", 1)
    
    # At this stage it's been a success, we need to update the board and player tiles
    new_tiles, new_bag = rules.pick_from_bag(the_game.game_bag, tiles=len(letters), existing_tiles=player_letters)
    
    the_game.board = rules.board_to_string(new_board)
    the_game.turn += 1
    the_game.game_bag = new_bag
    
    the_game.tiles[pnum] = player_letters + new_tiles
    the_game.tiles = tuple(the_game.tiles)
    
    # Set next player
    if pnum == the_game.players[-1]:
        pnum = -1
    
    the_game.current_player = the_game.players[pnum + 1]
    
    # Now add the move
    now = datetime.datetime.now()
    for word, score in words:
        move = WordyMove()
        
        move.game = the_game.id
        move.player = player_id
        
        move.word          = word
        move.score         = score
        move.game_turn     = the_game.turn
        move.timestamp     = now
        config['DBSession'].add(move)
    
    # achievements.check_after_move(player_id, words=words, points=points, letters_used=[l[0] for l in letters])
    
    # Do we need to end the game?
    if rules.scan_for_end(the_game):
        end_game(the_game)
        
        # for p in the_game.players:
        #     achievements.check_after_game_end(p, the_game)
        
        # achievements.check_after_game_win(the_game.winner, games_won(the_game.winner))
    
    config['DBSession'].add(the_game)
    return "success:"

def get_names(players):
    names = {}
    for i, n in config['DBSession'].query(config['User'].id, config['User'].name).filter(config['User'].id.in_(players)):
        names[i] = n
    return names

def end_game(the_game):
    game_moves = list(get_moves(the_game.id))
    scores = rules.tally_scores(the_game, game_moves, count_tiles=True)
    
    # Find winner
    highscore, highplayer = -1, ""
    draw = False
    for player, score in scores.items():
        if score > highscore:
            highscore = score
            highplayer = player
            draw = False
        elif score == highscore:
            highplayer = [highplayer, player]
            draw = True
    
    # Declare winner
    if not draw:
        the_game.winner = highplayer
    else:
        the_game.winner = -1

def completed_games(user_id, opponent_id=None):
    if opponent_id != None:
        filters = (
            "{:d} = ANY(wordy_games.players)".format(user_id),
            "{:d} = ANY(wordy_games.players)".format(opponent_id),
            WordyGame.winner != None,
        )
    else:
        filters = (
            "{:d} = ANY(wordy_games.players)".format(user_id),
            WordyGame.winner != None,
        )
    return config['DBSession'].query(func.count(WordyGame.id)).filter(*filters).first()[0]

def games_in_progress(user_id, opponent_id=None):
    if opponent_id != None:
        filters = (
            "{:d} = ANY(wordy_games.players)".format(user_id),
            "{:d} = ANY(wordy_games.players)".format(opponent_id),
            WordyGame.winner == None,
        )
    else:
        filters = (
            "{:d} = ANY(wordy_games.players)".format(user_id),
            WordyGame.winner == None,
        )
    return config['DBSession'].query(func.count(WordyGame.id)).filter(*filters).first()[0]
    
def games_won(user_id, opponent_id=None):
    filters = [
        WordyGame.winner == user_id,
    ]
    if opponent_id != None:
        filters.append(or_(
            "{:d} = ANY(wordy_games.players)".format(opponent_id),
        ))
    
    return config['DBSession'].query(func.count(WordyGame.id)).filter(*filters).first()[0]

def games_lost(user_id, opponent_id=None):
    if opponent_id != None:
        filters = (
            WordyGame.winner != user_id,
            WordyGame.winner != -1,
            WordyGame.winner != None,
            "{:d} = ANY(wordy_games.players)".format(user_id),
            "{:d} = ANY(wordy_games.players)".format(opponent_id),
        )
    else:
        filters = (
            WordyGame.winner != user_id,
            WordyGame.winner != -1,
            WordyGame.winner != None,
            "{:d} = ANY(wordy_games.players)".format(user_id),
        )
    return config['DBSession'].query(func.count(WordyGame.id)).filter(*filters).first()[0]

def games_drawn(user_id, opponent_id=None):
    if opponent_id != None:
        filters = (
            "{:d} = ANY(wordy_games.players)".format(user_id),
            "{:d} = ANY(wordy_games.players)".format(opponent_id),
            WordyGame.winner == -1,
        )
    else:
        
        filters = (
            "{:d} = ANY(wordy_games.players)".format(user_id),
            WordyGame.winner == -1,
        )
    return config['DBSession'].query(func.count(WordyGame.id)).filter(*filters).first()[0]

def get_stats(user_id, opponent_id=None):
    stats = dict(
        completed_games   = completed_games(user_id, opponent_id),
        games_in_progress = games_in_progress(user_id, opponent_id),
        
        games_won   = games_won(user_id, opponent_id),
        games_lost  = games_lost(user_id, opponent_id),
        games_drawn = games_drawn(user_id, opponent_id),
    )
    
    stats['win_ratio'] = rules.win_ratio(stats['games_won'], stats['completed_games'])
    
    return stats
