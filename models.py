from sqlalchemy import (
    Column,
    Boolean,
    DateTime,
    Integer,
    Text,
    String,
    ForeignKey,
    DateTime,
)

from sqlalchemy.dialects.postgresql import (
    ARRAY,
)

# You will need to point this to wherever your declarative base is
from ...models import Base

class WordyProfile(Base):
    __tablename__ = 'wordy_profiles'
    user          = Column(Integer, ForeignKey("users.id"), nullable=False, index=True, primary_key=True)
    
    matchmaking   = Column(Boolean, nullable=False, default=False)
    last_move     = Column(DateTime, default=False)
    
    wins          = Column(Integer, default=0, nullable=False)
    losses        = Column(Integer, default=0, nullable=False)

class WordyGame(Base):
    __tablename__ = 'wordy_games'
    id          = Column(Integer, primary_key=True)
    turn        = Column(Integer, nullable=False, default=0)
    source      = Column(Integer, ForeignKey("wordy_games.id"))
    rematch     = Column(Integer, ForeignKey("wordy_games.id"))
    # turn_log    = Column(Text, nullable=False, default='')
    
    # We're storing the board as a string because we shouldn't be asking for specific
    # parts of the board in database queries and we know the exact size and layout
    # of the board so we can easily pull pieces from it as if it were an array
    # while at the same time we're storing character data in it
    # It defaults to a blank board
    board       = Column(String, nullable=False, default=' '*255)
    started     = Column(DateTime, nullable=False)
    
    # Used beacuase it's a lot easier to query by this than a load of other stuff
    current_player = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    players     = Column(ARRAY(Integer), nullable=False, default=[])
    tiles       = Column(ARRAY(String), nullable=False, default=[])
    
    # The total tiles to pull from the bag for each player
    game_bag = Column(String, nullable=False, default="EEEEEEEEEEEEAAAAAAAAAIIIIIIIIIOOOOOOOONNNNNNRRRRRRTTTTTTLLLLSSSSUUUUDDDDGGGBBCCMMPPFFHHVVWWYYKJXQZ****")
    
    winner = Column(Integer, ForeignKey("users.id"), nullable=True)

# One move per word played, this means a player can make multiple moves in one
# go by making multiple words
class WordyMove(Base):
    __tablename__ = 'wordy_moves'
    id            = Column(Integer, primary_key=True)
    
    game          = Column(Integer, ForeignKey("wordy_games.id"), nullable=False)
    player        = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    word          = Column(String, nullable=False)
    score         = Column(Integer, nullable=False)
    game_turn     = Column(Integer, nullable=False)
    timestamp     = Column(DateTime, nullable=False)

class WordyWord(Base):
    __tablename__ = 'wordy_words'
    word = Column(String, nullable=False, primary_key=True)
