BEGIN;

CREATE TABLE wordy_words (
    word VARCHAR NOT NULL,
    PRIMARY KEY ("word")
);

CREATE TABLE wordy_profiles (
    "user" INTEGER NOT NULL,
    matchmaking BOOLEAN,
    last_move TIMESTAMP WITHOUT TIME ZONE,
    PRIMARY KEY ("user"),
    FOREIGN KEY("user") REFERENCES users (id)
);
CREATE INDEX ix_wordy_profiles_user ON wordy_profiles ("user");

CREATE TABLE wordy_games (
    id SERIAL NOT NULL,
    turn INTEGER,
    board VARCHAR NOT NULL,
    
    current_player INTEGER NOT NULL,
    started TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    players INTEGER[] NOT NULL,
    tiles VARCHAR[] NOT NULL,
    
    winner INTEGER,
    game_bag VARCHAR NOT NULL,
    
    rematch INTEGER,
    source INTEGER,
    
    PRIMARY KEY (id),
    FOREIGN KEY(current_player) REFERENCES users (id),
    FOREIGN KEY(winner) REFERENCES users (id),
    FOREIGN KEY(rematch) REFERENCES wordy_games (id),
    FOREIGN KEY(source) REFERENCES wordy_games (id)
);

CREATE TABLE wordy_moves (
    id SERIAL NOT NULL,
    game INTEGER NOT NULL,
    player INTEGER NOT NULL,
    word VARCHAR NOT NULL,
    score INTEGER NOT NULL,
    game_turn INTEGER NOT NULL,
    timestamp TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    
    PRIMARY KEY (id),
    FOREIGN KEY(game) REFERENCES wordy_games (id),
    FOREIGN KEY(player) REFERENCES users (id)
);
CREATE INDEX ix_wordy_moves_player ON wordy_moves (player);
CREATE INDEX ix_wordy_moves_game ON wordy_moves (game);

COMMIT;