-- Users Table
CREATE TABLE Users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    avatar_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

CREATE INDEX idx_users_username ON Users(username);
CREATE INDEX idx_users_email ON Users(email);

-- SocialLogins Table
CREATE TABLE SocialLogins (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    provider TEXT NOT NULL, -- e.g., 'google', 'apple'
    provider_user_id TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES Users(id),
    UNIQUE (provider, provider_user_id)
);

CREATE INDEX idx_sociallogins_user_id ON SocialLogins(user_id);
CREATE INDEX idx_sociallogins_provider_user_id ON SocialLogins(provider, provider_user_id);

-- Genres Table
CREATE TABLE Genres (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL -- e.g., Action, Romance, Sci-Fi
);

CREATE INDEX idx_genres_name ON Genres(name);

-- UserFavoriteGenres Table
CREATE TABLE UserFavoriteGenres (
    user_id INTEGER NOT NULL,
    genre_id INTEGER NOT NULL,
    PRIMARY KEY (user_id, genre_id),
    FOREIGN KEY (user_id) REFERENCES Users(id),
    FOREIGN KEY (genre_id) REFERENCES Genres(id)
);

CREATE INDEX idx_userfavoritegenres_user_id ON UserFavoriteGenres(user_id);
CREATE INDEX idx_userfavoritegenres_genre_id ON UserFavoriteGenres(genre_id);

-- Anime Table
CREATE TABLE Anime (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    release_year INTEGER,
    cover_image_url TEXT,
    average_rating REAL DEFAULT 0.0,
    language TEXT, -- e.g., 'Japanese', 'English'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP -- Handled by trigger/application logic for updates
);

CREATE INDEX idx_anime_title ON Anime(title);
CREATE INDEX idx_anime_release_year ON Anime(release_year);
CREATE INDEX idx_anime_language ON Anime(language);

-- AnimeGenres Table
CREATE TABLE AnimeGenres (
    anime_id INTEGER NOT NULL,
    genre_id INTEGER NOT NULL,
    PRIMARY KEY (anime_id, genre_id),
    FOREIGN KEY (anime_id) REFERENCES Anime(id),
    FOREIGN KEY (genre_id) REFERENCES Genres(id)
);

CREATE INDEX idx_animegenres_anime_id ON AnimeGenres(anime_id);
CREATE INDEX idx_animegenres_genre_id ON AnimeGenres(genre_id);

-- Tags Table
CREATE TABLE Tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL -- e.g., 'dark fantasy', 'mecha', 'isekai'
);

CREATE INDEX idx_tags_name ON Tags(name);

-- AnimeTags Table
CREATE TABLE AnimeTags (
    anime_id INTEGER NOT NULL,
    tag_id INTEGER NOT NULL,
    PRIMARY KEY (anime_id, tag_id),
    FOREIGN KEY (anime_id) REFERENCES Anime(id),
    FOREIGN KEY (tag_id) REFERENCES Tags(id)
);

CREATE INDEX idx_animetags_anime_id ON AnimeTags(anime_id);
CREATE INDEX idx_animetags_tag_id ON AnimeTags(tag_id);

-- Ratings Table
CREATE TABLE Ratings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    anime_id INTEGER NOT NULL,
    score INTEGER NOT NULL CHECK (score >= 1 AND score <= 10),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES Users(id),
    FOREIGN KEY (anime_id) REFERENCES Anime(id),
    UNIQUE (user_id, anime_id)
);

CREATE INDEX idx_ratings_user_id ON Ratings(user_id);
CREATE INDEX idx_ratings_anime_id ON Ratings(anime_id);

-- Reviews Table
CREATE TABLE Reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    anime_id INTEGER NOT NULL,
    rating_id INTEGER, -- Nullable, if a review must be tied to a rating
    text_content TEXT NOT NULL,
    is_spoiler BOOLEAN DEFAULT FALSE,
    upvotes INTEGER DEFAULT 0,
    downvotes INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- Handled by trigger/application logic for updates
    FOREIGN KEY (user_id) REFERENCES Users(id),
    FOREIGN KEY (anime_id) REFERENCES Anime(id),
    FOREIGN KEY (rating_id) REFERENCES Ratings(id)
);

CREATE INDEX idx_reviews_user_id ON Reviews(user_id);
CREATE INDEX idx_reviews_anime_id ON Reviews(anime_id);
CREATE INDEX idx_reviews_rating_id ON Reviews(rating_id);

-- ReviewVotes Table
CREATE TABLE ReviewVotes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    review_id INTEGER NOT NULL,
    vote_type TEXT NOT NULL CHECK (vote_type IN ('upvote', 'downvote')), -- Enum/String
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES Users(id),
    FOREIGN KEY (review_id) REFERENCES Reviews(id),
    UNIQUE (user_id, review_id)
);

CREATE INDEX idx_reviewvotes_user_id ON ReviewVotes(user_id);
CREATE INDEX idx_reviewvotes_review_id ON ReviewVotes(review_id);

-- WatchlistItems Table
CREATE TABLE WatchlistItems (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    anime_id INTEGER NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('plan_to_watch', 'completed', 'bookmarked', 'watching', 'dropped')), -- Enum/String
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES Users(id),
    FOREIGN KEY (anime_id) REFERENCES Anime(id),
    UNIQUE (user_id, anime_id, status)
);

CREATE INDEX idx_watchlistitems_user_id ON WatchlistItems(user_id);
CREATE INDEX idx_watchlistitems_anime_id ON WatchlistItems(anime_id);
CREATE INDEX idx_watchlistitems_status ON WatchlistItems(status);


-- Subcommunities Table
CREATE TABLE Subcommunities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL, -- e.g., "Action Lovers", "Slice of Life Fans"
    description TEXT,
    creator_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (creator_id) REFERENCES Users(id)
);

CREATE INDEX idx_subcommunities_name ON Subcommunities(name);
CREATE INDEX idx_subcommunities_creator_id ON Subcommunities(creator_id);

-- CommunityPosts Table
CREATE TABLE CommunityPosts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    subcommunity_id INTEGER, -- Nullable if posts can be general
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    post_type TEXT NOT NULL CHECK (post_type IN ('discussion', 'meme', 'theory', 'poll_question')), -- Enum/String
    upvotes INTEGER DEFAULT 0,
    downvotes INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- Handled by trigger/application logic for updates
    FOREIGN KEY (user_id) REFERENCES Users(id),
    FOREIGN KEY (subcommunity_id) REFERENCES Subcommunities(id)
);

CREATE INDEX idx_communityposts_user_id ON CommunityPosts(user_id);
CREATE INDEX idx_communityposts_subcommunity_id ON CommunityPosts(subcommunity_id);
CREATE INDEX idx_communityposts_title ON CommunityPosts(title);
CREATE INDEX idx_communityposts_post_type ON CommunityPosts(post_type);

-- PostVotes Table
CREATE TABLE PostVotes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    post_id INTEGER NOT NULL,
    vote_type TEXT NOT NULL CHECK (vote_type IN ('upvote', 'downvote')), -- Enum/String
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES Users(id),
    FOREIGN KEY (post_id) REFERENCES CommunityPosts(id),
    UNIQUE (user_id, post_id)
);

CREATE INDEX idx_postvotes_user_id ON PostVotes(user_id);
CREATE INDEX idx_postvotes_post_id ON PostVotes(post_id);

-- Comments Table
CREATE TABLE Comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    post_id INTEGER NOT NULL,
    parent_comment_id INTEGER, -- Nullable for top-level comments
    text_content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES Users(id),
    FOREIGN KEY (post_id) REFERENCES CommunityPosts(id),
    FOREIGN KEY (parent_comment_id) REFERENCES Comments(id)
);

CREATE INDEX idx_comments_user_id ON Comments(user_id);
CREATE INDEX idx_comments_post_id ON Comments(post_id);
CREATE INDEX idx_comments_parent_comment_id ON Comments(parent_comment_id);

-- PollOptions Table
CREATE TABLE PollOptions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    post_id INTEGER NOT NULL, -- where post_type is 'poll_question'
    option_text TEXT NOT NULL,
    FOREIGN KEY (post_id) REFERENCES CommunityPosts(id)
);

CREATE INDEX idx_polloptions_post_id ON PollOptions(post_id);

-- PollVotes Table
CREATE TABLE PollVotes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    poll_option_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES Users(id),
    FOREIGN KEY (poll_option_id) REFERENCES PollOptions(id),
    UNIQUE (user_id, poll_option_id) -- Assuming a user can only vote for one option in a poll
);

CREATE INDEX idx_pollvotes_user_id ON PollVotes(user_id);
CREATE INDEX idx_pollvotes_poll_option_id ON PollVotes(poll_option_id);

-- AnimeClubs Table
CREATE TABLE AnimeClubs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    creator_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (creator_id) REFERENCES Users(id)
);

CREATE INDEX idx_animeclubs_name ON AnimeClubs(name);
CREATE INDEX idx_animeclubs_creator_id ON AnimeClubs(creator_id);

-- ClubMemberships Table
CREATE TABLE ClubMemberships (
    user_id INTEGER NOT NULL,
    club_id INTEGER NOT NULL,
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, club_id),
    FOREIGN KEY (user_id) REFERENCES Users(id),
    FOREIGN KEY (club_id) REFERENCES AnimeClubs(id)
);

CREATE INDEX idx_clubmemberships_user_id ON ClubMemberships(user_id);
CREATE INDEX idx_clubmemberships_club_id ON ClubMemberships(club_id);

-- ClubWatchSchedules Table
CREATE TABLE ClubWatchSchedules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    club_id INTEGER NOT NULL,
    anime_id INTEGER NOT NULL,
    start_date DATE,
    end_date DATE,
    discussion_day TEXT, -- Enum/String: 'Monday', 'Tuesday', etc. or specific date
    FOREIGN KEY (club_id) REFERENCES AnimeClubs(id),
    FOREIGN KEY (anime_id) REFERENCES Anime(id)
);

CREATE INDEX idx_clubwatchschedules_club_id ON ClubWatchSchedules(club_id);
CREATE INDEX idx_clubwatchschedules_anime_id ON ClubWatchSchedules(anime_id);

-- Notifications Table
CREATE TABLE Notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL, -- the recipient
    type TEXT NOT NULL CHECK (type IN ('new_recommendation', 'friend_activity', 'community_update', 'new_follower', 'review_reply', 'post_reply', 'friend_request')), -- Enum/String
    content TEXT NOT NULL,
    link_url TEXT, -- to navigate to the relevant content
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES Users(id)
);

CREATE INDEX idx_notifications_user_id ON Notifications(user_id);
CREATE INDEX idx_notifications_is_read ON Notifications(is_read);

-- Friendships Table
CREATE TABLE Friendships (
    user_id_1 INTEGER NOT NULL,
    user_id_2 INTEGER NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('pending', 'accepted', 'blocked')), -- Enum/String
    requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    accepted_at TIMESTAMP,
    PRIMARY KEY (user_id_1, user_id_2),
    FOREIGN KEY (user_id_1) REFERENCES Users(id),
    FOREIGN KEY (user_id_2) REFERENCES Users(id),
    CHECK (user_id_1 < user_id_2) -- Ensures uniqueness of pairs and avoids redundant entries
);

CREATE INDEX idx_friendships_user_id_1 ON Friendships(user_id_1);
CREATE INDEX idx_friendships_user_id_2 ON Friendships(user_id_2);
CREATE INDEX idx_friendships_status ON Friendships(status);

-- DirectMessages Table
CREATE TABLE DirectMessages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sender_id INTEGER NOT NULL,
    receiver_id INTEGER NOT NULL,
    message_content TEXT NOT NULL,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_read BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (sender_id) REFERENCES Users(id),
    FOREIGN KEY (receiver_id) REFERENCES Users(id)
);

CREATE INDEX idx_directmessages_sender_id ON DirectMessages(sender_id);
CREATE INDEX idx_directmessages_receiver_id ON DirectMessages(receiver_id);
CREATE INDEX idx_directmessages_sent_at ON DirectMessages(sent_at);

-- Triggers for updated_at columns (example for Anime table, similar can be created for others)
-- SQLite does not directly support ON UPDATE CURRENT_TIMESTAMP for table definitions.
-- This needs to be handled by triggers.
CREATE TRIGGER update_anime_updated_at
AFTER UPDATE ON Anime
FOR EACH ROW
BEGIN
    UPDATE Anime SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
END;

CREATE TRIGGER update_reviews_updated_at
AFTER UPDATE ON Reviews
FOR EACH ROW
BEGIN
    UPDATE Reviews SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
END;

CREATE TRIGGER update_communityposts_updated_at
AFTER UPDATE ON CommunityPosts
FOR EACH ROW
BEGIN
    UPDATE CommunityPosts SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
END;

-- Note: For other tables like Reviews, CommunityPosts that have an updated_at column,
-- similar triggers would be needed if using SQLite.
-- For PostgreSQL or MySQL, `ON UPDATE CURRENT_TIMESTAMP` can often be part of the table definition.
-- Example for PostgreSQL: updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP;
-- Example for MySQL: updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP;
-- Since this is a general SQL file, I've used SQLite compatible triggers as an example.
-- If a specific RDBMS is targeted, these trigger definitions might change or be unnecessary.

-- Further considerations:
-- - Cascading deletes: ON DELETE CASCADE might be useful for some foreign key relationships
--   (e.g., if a User is deleted, their SocialLogins, Ratings, Reviews, etc., might also be deleted).
--   This has been omitted for now for simplicity but is an important design decision.
-- - Check constraints for ENUM-like text fields could be more robust depending on the RDBMS.
--   SQLite's CHECK constraint is used here.
-- - The `language` field in Anime, `discussion_day` in ClubWatchSchedules, `vote_type` in ReviewVotes/PostVotes,
--   `status` in WatchlistItems, `post_type` in CommunityPosts, `type` in Notifications, and `status` in Friendships
--   are defined as TEXT with CHECK constraints. In some RDBMS, these could be actual ENUM types.
