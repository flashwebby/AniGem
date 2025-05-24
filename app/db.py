import sqlite3
import click
from flask import current_app, g
from flask.cli import with_appcontext
from app.models.user import User # Assuming User model is in app.models.user

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(
            current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    db = get_db()
    with current_app.open_resource('schema.sql') as f:
        db.executescript(f.read().decode('utf8'))

@click.command('init-db')
@with_appcontext
def init_db_command():
    """Clear the existing data and create new tables."""
    init_db()
    click.echo('Initialized the database.')

def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
    app.config['DATABASE'] = 'instance/flaskr.sqlite' # Added this line, common practice for flask

# User specific database functions
def add_user(username, email, password):
    """Adds a new user to the database."""
    db = get_db()
    user_obj = User(id=None, username=username, email=email, password_hash=None)
    user_obj.set_password(password)
    try:
        cursor = db.execute(
            "INSERT INTO Users (username, email, password_hash) VALUES (?, ?, ?)",
            (user_obj.username, user_obj.email, user_obj.password_hash)
        )
        db.commit()
        return cursor.lastrowid # Return the id of the newly inserted user
    except sqlite3.IntegrityError as e:
        # This could be due to UNIQUE constraint violation (username or email)
        print(f"Error adding user: {e}")
        return None

def find_user_by_id(user_id):
    """Finds a user by their ID."""
    db = get_db()
    cursor = db.execute("SELECT * FROM Users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    if row:
        return User(**row)
    return None

def find_user_by_username(username):
    """Finds a user by their username."""
    db = get_db()
    cursor = db.execute("SELECT * FROM Users WHERE username = ?", (username,))
    row = cursor.fetchone()
    if row:
        return User(**row)
    return None

def find_user_by_email(email):
    """Finds a user by their email address."""
    db = get_db()
    cursor = db.execute("SELECT * FROM Users WHERE email = ?", (email,))
    row = cursor.fetchone()
    if row:
        return User(**row)
    return None

def update_user_last_login(user_id):
    """Updates the last_login timestamp for a user."""
    db = get_db()
    try:
        db.execute(
            "UPDATE Users SET last_login = CURRENT_TIMESTAMP WHERE id = ?",
            (user_id,)
        )
        db.commit()
        return True
    except sqlite3.Error as e:
        print(f"Error updating last_login: {e}")
        return False

# Genre specific database functions
def add_genre(name):
    """Adds a new genre to the database."""
    db = get_db()
    try:
        cursor = db.execute("INSERT INTO Genres (name) VALUES (?)", (name,))
        db.commit()
        return cursor.lastrowid
    except sqlite3.IntegrityError: # Genre name is unique
        return get_genre_by_name(name).id # Return existing genre's id
    except sqlite3.Error as e:
        print(f"Error adding genre: {e}")
        return None

def get_genre_by_id(genre_id):
    from app.models.taxonomy import Genre
    db = get_db()
    row = db.execute("SELECT * FROM Genres WHERE id = ?", (genre_id,)).fetchone()
    return Genre(**row) if row else None

def get_genre_by_name(name):
    from app.models.taxonomy import Genre
    db = get_db()
    row = db.execute("SELECT * FROM Genres WHERE name = ?", (name,)).fetchone()
    return Genre(**row) if row else None

def get_all_genres():
    from app.models.taxonomy import Genre
    db = get_db()
    rows = db.execute("SELECT * FROM Genres ORDER BY name").fetchall()
    return [Genre(**row) for row in rows]

# Tag specific database functions
def add_tag(name):
    """Adds a new tag to the database."""
    db = get_db()
    try:
        cursor = db.execute("INSERT INTO Tags (name) VALUES (?)", (name,))
        db.commit()
        return cursor.lastrowid
    except sqlite3.IntegrityError: # Tag name is unique
        return get_tag_by_name(name).id # Return existing tag's id
    except sqlite3.Error as e:
        print(f"Error adding tag: {e}")
        return None

def get_tag_by_id(tag_id):
    from app.models.taxonomy import Tag
    db = get_db()
    row = db.execute("SELECT * FROM Tags WHERE id = ?", (tag_id,)).fetchone()
    return Tag(**row) if row else None

def get_tag_by_name(name):
    from app.models.taxonomy import Tag
    db = get_db()
    row = db.execute("SELECT * FROM Tags WHERE name = ?", (name,)).fetchone()
    return Tag(**row) if row else None

def get_all_tags():
    from app.models.taxonomy import Tag
    db = get_db()
    rows = db.execute("SELECT * FROM Tags ORDER BY name").fetchall()
    return [Tag(**row) for row in rows]

# Anime specific database functions
def add_anime(title, description=None, release_year=None, cover_image_url=None, language=None, genre_names=None, tag_names=None):
    """
    Adds a new anime to the database and links it to genres and tags.
    genre_names and tag_names should be lists of strings.
    """
    db = get_db()
    try:
        cursor = db.execute(
            """INSERT INTO Anime (title, description, release_year, cover_image_url, language)
               VALUES (?, ?, ?, ?, ?)""",
            (title, description, release_year, cover_image_url, language)
        )
        anime_id = cursor.lastrowid

        if genre_names:
            for genre_name in genre_names:
                genre = get_genre_by_name(genre_name)
                if not genre: # If genre doesn't exist, add it
                    genre_id = add_genre(genre_name)
                    if genre_id:
                        link_anime_to_genre(anime_id, genre_id)
                else:
                    link_anime_to_genre(anime_id, genre.id)
        
        if tag_names:
            for tag_name in tag_names:
                tag = get_tag_by_name(tag_name)
                if not tag: # If tag doesn't exist, add it
                    tag_id = add_tag(tag_name)
                    if tag_id:
                        link_anime_to_tag(anime_id, tag_id)
                else:
                    link_anime_to_tag(anime_id, tag.id)
        
        db.commit()
        return anime_id
    except sqlite3.Error as e:
        db.rollback()
        print(f"Error adding anime: {e}")
        return None

def link_anime_to_genre(anime_id, genre_id):
    db = get_db()
    try:
        db.execute("INSERT INTO AnimeGenres (anime_id, genre_id) VALUES (?, ?)", (anime_id, genre_id))
        # db.commit() # Commit is usually handled by the calling function (e.g., add_anime)
    except sqlite3.IntegrityError: # Handles cases where the link already exists
        pass
    except sqlite3.Error as e:
        print(f"Error linking anime {anime_id} to genre {genre_id}: {e}")

def link_anime_to_tag(anime_id, tag_id):
    db = get_db()
    try:
        db.execute("INSERT INTO AnimeTags (anime_id, tag_id) VALUES (?, ?)", (anime_id, tag_id))
        # db.commit() # Commit is usually handled by the calling function (e.g., add_anime)
    except sqlite3.IntegrityError: # Handles cases where the link already exists
        pass
    except sqlite3.Error as e:
        print(f"Error linking anime {anime_id} to tag {tag_id}: {e}")

def get_anime_by_id(anime_id):
    from app.models.anime import Anime
    from app.models.taxonomy import Genre, Tag
    db = get_db()
    
    anime_row = db.execute("SELECT * FROM Anime WHERE id = ?", (anime_id,)).fetchone()
    if not anime_row:
        return None

    # Fetch genres for the anime
    genre_rows = db.execute(
        """SELECT g.id, g.name FROM Genres g
           JOIN AnimeGenres ag ON g.id = ag.genre_id
           WHERE ag.anime_id = ?""", (anime_id,)
    ).fetchall()
    genres = [Genre(**row) for row in genre_rows]

    # Fetch tags for the anime
    tag_rows = db.execute(
        """SELECT t.id, t.name FROM Tags t
           JOIN AnimeTags at ON t.id = at.tag_id
           WHERE at.anime_id = ?""", (anime_id,)
    ).fetchall()
    tags = [Tag(**row) for row in tag_rows]
    
    # Create Anime object with its genres and tags
    anime_data = dict(anime_row) # Convert sqlite3.Row to dict
    return Anime(**anime_data, genres=genres, tags=tags)


def get_all_anime(filters=None):
    from app.models.anime import Anime
    from app.models.taxonomy import Genre, Tag # Needed for constructing objects if fetching details here
    db = get_db()
    
    query = "SELECT DISTINCT a.id, a.title, a.description, a.release_year, a.cover_image_url, a.average_rating, a.language, a.created_at, a.updated_at FROM Anime a"
    conditions = []
    params = []

    if filters:
        if filters.get('genre_id'):
            query += " JOIN AnimeGenres ag ON a.id = ag.anime_id"
            conditions.append("ag.genre_id = ?")
            params.append(filters['genre_id'])
        if filters.get('tag_id'): # Assuming filtering by a single tag ID for now
            query += " JOIN AnimeTags at ON a.id = at.tag_id"
            conditions.append("at.tag_id = ?")
            params.append(filters['tag_id'])
        if filters.get('release_year'):
            conditions.append("a.release_year = ?")
            params.append(filters['release_year'])
        if filters.get('language'):
            conditions.append("a.language = ?")
            params.append(filters['language'])

    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    
    query += " ORDER BY a.title" # Default ordering

    rows = db.execute(query, params).fetchall()
    
    # For simplicity, this function returns a list of basic Anime objects without genre/tag details.
    # If full details are needed for each anime in the list, we'd need to loop and call get_anime_by_id
    # or expand the query to fetch all related data (which can get complex with many-to-many).
    # For a list view, this is often sufficient, and details are fetched on demand for a single anime view.
    anime_list = []
    for row in rows:
        # To get genres and tags for each anime in the list, we would need N+1 queries or a more complex join.
        # For now, let's fetch them individually for simplicity in this example, though it's not the most performant for large lists.
        # A better approach for list views might be to just show genre/tag names as strings from a joined query.
        anime_obj = get_anime_by_id(row['id']) # This will fetch genres/tags for each anime
        if anime_obj:
            anime_list.append(anime_obj)
            
    return anime_list


def get_random_anime():
    db = get_db()
    row = db.execute("SELECT id FROM Anime ORDER BY RANDOM() LIMIT 1").fetchone()
    if row:
        return get_anime_by_id(row['id'])
    return None

def update_anime_average_rating(anime_id):
    """
    Updates the average_rating for an anime based on scores in the Ratings table.
    This should be called when a new rating is added or an existing one is updated/deleted.
    """
    db = get_db()
    try:
        cursor = db.execute(
            """SELECT AVG(score) as avg_score FROM Ratings WHERE anime_id = ?""",
            (anime_id,)
        )
        result = cursor.fetchone()
        avg_score = result['avg_score'] if result['avg_score'] is not None else 0.0
        
        db.execute(
            "UPDATE Anime SET average_rating = ? WHERE id = ?",
            (avg_score, anime_id)
        )
        db.commit()
        return True
    except sqlite3.Error as e:
        print(f"Error updating average rating for anime {anime_id}: {e}")
        db.rollback()
        return False

# Seed data function (can be expanded)
def seed_db():
    """Seeds the database with initial data for genres, tags, and anime."""
    db = get_db() # Ensure db is available

    # Add Genres
    genres_to_add = ["Action", "Comedy", "Drama", "Sci-Fi", "Fantasy", "Slice of Life", "Romance", "Thriller", "Adventure"]
    genre_ids = {}
    for genre_name in genres_to_add:
        genre_id = add_genre(genre_name)
        if genre_id:
            genre_ids[genre_name] = genre_id
            click.echo(f"Added/found genre: {genre_name}")

    # Add Tags
    tags_to_add = ["Mecha", "Magic", "Shounen", "Shoujo", "Isekai", "Post-Apocalyptic", "Historical", "School Life", "Vampire"]
    tag_ids = {}
    for tag_name in tags_to_add:
        tag_id = add_tag(tag_name)
        if tag_id:
            tag_ids[tag_name] = tag_id
            click.echo(f"Added/found tag: {tag_name}")

    # Add Sample Anime
    sample_anime = [
        {
            "title": "Code Geass: Lelouch of the Rebellion",
            "description": "In an alternate timeline, Japan, now known as Area 11, is conquered by the Holy Britannian Empire. Lelouch vi Britannia, an exiled Britannian prince, obtains a mysterious power called Geass and leads a rebellion against the Empire.",
            "release_year": 2006,
            "language": "Japanese",
            "cover_image_url": "https://cdn.myanimelist.net/images/anime/5/50331.jpg",
            "genre_names": ["Action", "Sci-Fi", "Drama", "Mecha"],
            "tag_names": ["Mecha", "Magic", "Shounen"]
        },
        {
            "title": "Attack on Titan",
            "description": "After his hometown is destroyed and his mother is killed, young Eren Jaeger vows to cleanse the earth of the giant humanoid Titans that have brought humanity to the brink of extinction.",
            "release_year": 2013,
            "language": "Japanese",
            "cover_image_url": "https://cdn.myanimelist.net/images/anime/10/47347.jpg",
            "genre_names": ["Action", "Fantasy", "Drama", "Thriller"],
            "tag_names": ["Post-Apocalyptic", "Shounen"]
        },
        {
            "title": "K-On!",
            "description": "Four high school girls join the light music club of Sakuragaoka Girl's High School to try to save it from being disbanded. However, they are the only members of the club.",
            "release_year": 2009,
            "language": "Japanese",
            "cover_image_url": "https://cdn.myanimelist.net/images/anime/10/76120.jpg",
            "genre_names": ["Slice of Life", "Comedy"],
            "tag_names": ["School Life"]
        },
        {
            "title": "Your Name.",
            "description": "Two teenagers share a profound, magical connection upon discovering they are swapping bodies. Things manage to become even more complicated when the boy and girl decide to meet in person.",
            "release_year": 2016,
            "language": "Japanese",
            "cover_image_url": "https://cdn.myanimelist.net/images/anime/5/87048.jpg",
            "genre_names": ["Romance", "Drama", "Fantasy"],
            "tag_names": ["Magic"]
        }
    ]

    for anime_data in sample_anime:
        anime_id = add_anime(
            title=anime_data["title"],
            description=anime_data["description"],
            release_year=anime_data["release_year"],
            language=anime_data["language"],
            cover_image_url=anime_data["cover_image_url"],
            genre_names=anime_data["genre_names"],
            tag_names=anime_data["tag_names"]
        )
        if anime_id:
            click.echo(f"Added anime: {anime_data['title']} (ID: {anime_id})")
        else:
            click.echo(f"Failed to add anime: {anime_data['title']}")
    
    # Initialize average ratings (assuming no ratings exist yet, so they'll be 0)
    all_anime_for_ratings = get_all_anime()
    for anime_item in all_anime_for_ratings:
        update_anime_average_rating(anime_item.id)
        click.echo(f"Initialized average rating for anime ID: {anime_item.id}")


@click.command('seed-db')
@with_appcontext
def seed_db_command():
    """Seed the database with initial sample data."""
    init_db() # Ensure tables are created
    click.echo("Seeding the database...")
    seed_db()
    click.echo("Database seeded.")

# Modify init_app to include the seed_db_command
def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
    app.cli.add_command(seed_db_command) # Add the new command
    app.config['DATABASE'] = 'instance/flaskr.sqlite'


# Rating specific database functions
def add_or_update_rating(user_id, anime_id, score):
    """Adds a new rating or updates an existing one for a user and anime."""
    db = get_db()
    try:
        # Check if a rating already exists
        existing_rating = db.execute(
            "SELECT id FROM Ratings WHERE user_id = ? AND anime_id = ?",
            (user_id, anime_id)
        ).fetchone()

        if existing_rating:
            # Update existing rating
            db.execute(
                "UPDATE Ratings SET score = ?, created_at = CURRENT_TIMESTAMP WHERE id = ?",
                (score, existing_rating['id'])
            )
            rating_id = existing_rating['id']
        else:
            # Insert new rating
            cursor = db.execute(
                "INSERT INTO Ratings (user_id, anime_id, score) VALUES (?, ?, ?)",
                (user_id, anime_id, score)
            )
            rating_id = cursor.lastrowid
        
        db.commit()
        update_anime_average_rating(anime_id) # Update anime's average rating
        return rating_id
    except sqlite3.Error as e:
        db.rollback()
        print(f"Error adding/updating rating: {e}")
        return None

def get_user_rating_for_anime(user_id, anime_id):
    from app.models.ratings_reviews import Rating
    db = get_db()
    row = db.execute(
        "SELECT * FROM Ratings WHERE user_id = ? AND anime_id = ?",
        (user_id, anime_id)
    ).fetchone()
    return Rating(**row) if row else None

# Review specific database functions
def add_review(user_id, anime_id, text_content, rating_id=None, is_spoiler=False):
    """Adds a new review for an anime by a user."""
    db = get_db()
    try:
        cursor = db.execute(
            """INSERT INTO Reviews (user_id, anime_id, rating_id, text_content, is_spoiler)
               VALUES (?, ?, ?, ?, ?)""",
            (user_id, anime_id, rating_id, text_content, is_spoiler)
        )
        db.commit()
        return cursor.lastrowid
    except sqlite3.Error as e:
        db.rollback()
        print(f"Error adding review: {e}")
        return None

def get_reviews_for_anime(anime_id):
    from app.models.ratings_reviews import Review
    from app.models.user import User # To get user details
    db = get_db()
    rows = db.execute(
        """SELECT r.id, r.user_id, r.anime_id, r.rating_id, r.text_content, r.is_spoiler,
                  r.upvotes, r.downvotes, r.created_at, r.updated_at,
                  u.username, u.avatar_url, rat.score as rating_score
           FROM Reviews r
           JOIN Users u ON r.user_id = u.id
           LEFT JOIN Ratings rat ON r.rating_id = rat.id
           WHERE r.anime_id = ?
           ORDER BY r.created_at DESC""",
        (anime_id,)
    ).fetchall()

    reviews = []
    for row_data in rows:
        row = dict(row_data) # Convert sqlite3.Row to dict
        user_data = User(id=row['user_id'], username=row['username'], email=None, password_hash=None, avatar_url=row['avatar_url'])
        # We are primarily interested in username and avatar for display with the review
        
        # Create a dictionary for the review data, excluding user-specific fields already captured
        review_data = {k: row[k] for k in row if k not in ['username', 'avatar_url']}
        review_obj = Review(**review_data)
        review_obj.user = user_data # Attach the User object (or just username/avatar)
        review_obj.rating_score = row['rating_score'] # Attach associated rating score
        reviews.append(review_obj)
    return reviews

# ReviewVote specific database functions
def add_or_update_review_vote(user_id, review_id, vote_type):
    """Adds or updates a user's vote for a review. vote_type should be 'upvote' or 'downvote'."""
    db = get_db()
    if vote_type not in ['upvote', 'downvote']:
        print(f"Invalid vote_type: {vote_type}")
        return None
    
    try:
        existing_vote = db.execute(
            "SELECT id, vote_type FROM ReviewVotes WHERE user_id = ? AND review_id = ?",
            (user_id, review_id)
        ).fetchone()

        if existing_vote:
            if existing_vote['vote_type'] == vote_type:
                # User clicked the same vote type again, remove the vote (toggle off)
                db.execute("DELETE FROM ReviewVotes WHERE id = ?", (existing_vote['id'],))
            else:
                # User changed their vote
                db.execute(
                    "UPDATE ReviewVotes SET vote_type = ?, created_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (vote_type, existing_vote['id'])
                )
        else:
            # New vote
            db.execute(
                "INSERT INTO ReviewVotes (user_id, review_id, vote_type) VALUES (?, ?, ?)",
                (user_id, review_id, vote_type)
            )
        
        db.commit()
        update_review_vote_counts(review_id) # Update review's vote counts
        return True
    except sqlite3.Error as e:
        db.rollback()
        print(f"Error adding/updating review vote: {e}")
        return None

def update_review_vote_counts(review_id):
    """Updates the upvotes and downvotes counts for a review."""
    db = get_db()
    try:
        upvotes = db.execute(
            "SELECT COUNT(id) FROM ReviewVotes WHERE review_id = ? AND vote_type = 'upvote'",
            (review_id,)
        ).fetchone()[0]
        
        downvotes = db.execute(
            "SELECT COUNT(id) FROM ReviewVotes WHERE review_id = ? AND vote_type = 'downvote'",
            (review_id,)
        ).fetchone()[0]
        
        db.execute(
            "UPDATE Reviews SET upvotes = ?, downvotes = ? WHERE id = ?",
            (upvotes, downvotes, review_id)
        )
        db.commit()
    except sqlite3.Error as e:
        db.rollback()
        print(f"Error updating review vote counts for review {review_id}: {e}")

def get_user_vote_for_review(user_id, review_id):
    """Gets the user's current vote for a review, if any."""
    db = get_db()
    row = db.execute(
        "SELECT vote_type FROM ReviewVotes WHERE user_id = ? AND review_id = ?",
        (user_id, review_id)
    ).fetchone()
    return row['vote_type'] if row else None

def get_review_by_id(review_id):
    from app.models.ratings_reviews import Review
    from app.models.user import User
    db = get_db()
    row_data = db.execute(
        """SELECT r.*, u.username, u.avatar_url, rat.score as rating_score
           FROM Reviews r
           JOIN Users u ON r.user_id = u.id
           LEFT JOIN Ratings rat ON r.rating_id = rat.id
           WHERE r.id = ?""",
        (review_id,)
    ).fetchone()

    if not row_data:
        return None

    row = dict(row_data)
    user_data = User(id=row['user_id'], username=row['username'], email=None, password_hash=None, avatar_url=row['avatar_url'])
    
    review_data = {k: row[k] for k in row if k not in ['username', 'avatar_url', 'rating_score']}
    review_obj = Review(**review_data)
    review_obj.user = user_data
    review_obj.rating_score = row['rating_score']
    return review_obj

# Subcommunity specific database functions
def add_subcommunity(name, description, creator_id):
    from app.models.community import Subcommunity
    db = get_db()
    try:
        cursor = db.execute(
            "INSERT INTO Subcommunities (name, description, creator_id) VALUES (?, ?, ?)",
            (name, description, creator_id)
        )
        db.commit()
        subcommunity_id = cursor.lastrowid
        # Fetch the creator's username for the Subcommunity object
        user = find_user_by_id(creator_id)
        return Subcommunity(id=subcommunity_id, name=name, description=description, creator_id=creator_id, creator_username=user.username if user else "Unknown")
    except sqlite3.IntegrityError: # Name might need to be unique
        db.rollback()
        print(f"Error: Subcommunity with name '{name}' might already exist.")
        return None
    except sqlite3.Error as e:
        db.rollback()
        print(f"Error adding subcommunity: {e}")
        return None

def get_subcommunity_by_id(subcommunity_id):
    from app.models.community import Subcommunity
    db = get_db()
    row = db.execute(
        """SELECT s.*, u.username as creator_username 
           FROM Subcommunities s JOIN Users u ON s.creator_id = u.id 
           WHERE s.id = ?""", (subcommunity_id,)
    ).fetchone()
    return Subcommunity(**row) if row else None

def get_subcommunity_by_name(name):
    from app.models.community import Subcommunity
    db = get_db()
    row = db.execute(
        """SELECT s.*, u.username as creator_username 
           FROM Subcommunities s JOIN Users u ON s.creator_id = u.id 
           WHERE s.name = ?""", (name,)
    ).fetchone()
    return Subcommunity(**row) if row else None

def get_all_subcommunities():
    from app.models.community import Subcommunity
    db = get_db()
    rows = db.execute(
        """SELECT s.*, u.username as creator_username
           FROM Subcommunities s JOIN Users u ON s.creator_id = u.id
           ORDER BY s.created_at DESC"""
    ).fetchall()
    return [Subcommunity(**row) for row in rows]


# Community Post specific database functions
def add_post(user_id, title, content, subcommunity_id=None, post_type='discussion'):
    db = get_db()
    try:
        cursor = db.execute(
            """INSERT INTO CommunityPosts (user_id, title, content, subcommunity_id, post_type)
               VALUES (?, ?, ?, ?, ?)""",
            (user_id, title, content, subcommunity_id, post_type)
        )
        db.commit()
        return cursor.lastrowid
    except sqlite3.Error as e:
        db.rollback()
        print(f"Error adding post: {e}")
        return None

def get_post_by_id(post_id):
    from app.models.community import CommunityPost, Subcommunity
    from app.models.user import User
    db = get_db()
    row = db.execute(
        """SELECT cp.*, u.username, u.avatar_url, s.name as subcommunity_name
           FROM CommunityPosts cp
           JOIN Users u ON cp.user_id = u.id
           LEFT JOIN Subcommunities s ON cp.subcommunity_id = s.id
           WHERE cp.id = ?""",
        (post_id,)
    ).fetchone()

    if not row:
        return None

    post_data = dict(row)
    user = User(id=row['user_id'], username=row['username'], email=None, password_hash=None, avatar_url=row['avatar_url'])
    subcommunity = None
    if row['subcommunity_id']:
        # Minimal subcommunity object for now, or call get_subcommunity_by_id if full object needed
        subcommunity = Subcommunity(id=row['subcommunity_id'], name=row['subcommunity_name']) 
    
    # Fetch comment count
    comment_count = db.execute("SELECT COUNT(id) FROM Comments WHERE post_id = ?", (post_id,)).fetchone()[0]

    post = CommunityPost(
        id=post_data['id'], user_id=post_data['user_id'], title=post_data['title'],
        content=post_data['content'], subcommunity_id=post_data['subcommunity_id'],
        post_type=post_data['post_type'], upvotes=post_data['upvotes'],
        downvotes=post_data['downvotes'], created_at=post_data['created_at'],
        updated_at=post_data['updated_at'], user=user, subcommunity=subcommunity,
        comment_count=comment_count
    )
    return post

def get_posts_for_subcommunity(subcommunity_id, limit=20, offset=0):
    # Similar to get_all_posts but filtered and with pagination
    return _get_posts_query(subcommunity_id=subcommunity_id, limit=limit, offset=offset)

def get_all_posts(limit=20, offset=0):
    # Generic function to get posts, can be used for main feed
    return _get_posts_query(limit=limit, offset=offset)

def _get_posts_query(subcommunity_id=None, user_id=None, limit=20, offset=0):
    from app.models.community import CommunityPost, Subcommunity
    from app.models.user import User
    db = get_db()
    
    query = """
        SELECT cp.id, cp.title, cp.user_id, cp.subcommunity_id, cp.post_type, 
               cp.upvotes, cp.downvotes, cp.created_at,
               u.username, u.avatar_url, s.name as subcommunity_name,
               (SELECT COUNT(id) FROM Comments WHERE post_id = cp.id) as comment_count
        FROM CommunityPosts cp
        JOIN Users u ON cp.user_id = u.id
        LEFT JOIN Subcommunities s ON cp.subcommunity_id = s.id
    """
    params = []
    conditions = []

    if subcommunity_id:
        conditions.append("cp.subcommunity_id = ?")
        params.append(subcommunity_id)
    if user_id: # For fetching posts by a specific user
        conditions.append("cp.user_id = ?")
        params.append(user_id)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    
    query += " ORDER BY cp.created_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    
    rows = db.execute(query, params).fetchall()
    
    posts = []
    for row_data in rows:
        row = dict(row_data)
        user = User(id=row['user_id'], username=row['username'], email=None, password_hash=None, avatar_url=row['avatar_url'])
        subcommunity = None
        if row['subcommunity_id'] and row['subcommunity_name']:
            subcommunity = Subcommunity(id=row['subcommunity_id'], name=row['subcommunity_name'])
        
        posts.append(CommunityPost(
            id=row['id'], title=row['title'], user_id=row['user_id'], 
            subcommunity_id=row['subcommunity_id'], post_type=row['post_type'],
            upvotes=row['upvotes'], downvotes=row['downvotes'], created_at=row['created_at'],
            user=user, subcommunity=subcommunity, comment_count=row['comment_count'],
            content="" # Content is not fetched in list view for brevity
        ))
    return posts


def update_post_vote_counts(post_id):
    db = get_db()
    try:
        upvotes = db.execute(
            "SELECT COUNT(id) FROM PostVotes WHERE post_id = ? AND vote_type = 'upvote'", (post_id,)
        ).fetchone()[0]
        downvotes = db.execute(
            "SELECT COUNT(id) FROM PostVotes WHERE post_id = ? AND vote_type = 'downvote'", (post_id,)
        ).fetchone()[0]
        
        db.execute(
            "UPDATE CommunityPosts SET upvotes = ?, downvotes = ? WHERE id = ?",
            (upvotes, downvotes, post_id)
        )
        db.commit()
    except sqlite3.Error as e:
        db.rollback()
        print(f"Error updating post vote counts for post {post_id}: {e}")

# PostVote specific database functions
def add_or_update_post_vote(user_id, post_id, vote_type):
    db = get_db()
    if vote_type not in ['upvote', 'downvote']:
        return None
    try:
        existing_vote = db.execute(
            "SELECT id, vote_type FROM PostVotes WHERE user_id = ? AND post_id = ?",
            (user_id, post_id)
        ).fetchone()

        if existing_vote:
            if existing_vote['vote_type'] == vote_type: # Clicked same vote again (toggle off)
                db.execute("DELETE FROM PostVotes WHERE id = ?", (existing_vote['id'],))
            else: # Changed vote
                db.execute("UPDATE PostVotes SET vote_type = ? WHERE id = ?", (vote_type, existing_vote['id']))
        else: # New vote
            db.execute("INSERT INTO PostVotes (user_id, post_id, vote_type) VALUES (?, ?, ?)",
                       (user_id, post_id, vote_type))
        db.commit()
        update_post_vote_counts(post_id)
        return True
    except sqlite3.Error as e:
        db.rollback()
        print(f"Error adding/updating post vote: {e}")
        return False

def get_user_vote_for_post(user_id, post_id):
    db = get_db()
    row = db.execute("SELECT vote_type FROM PostVotes WHERE user_id = ? AND post_id = ?", (user_id, post_id)).fetchone()
    return row['vote_type'] if row else None


# Comment specific database functions
def add_comment(user_id, post_id, text_content, parent_comment_id=None):
    db = get_db()
    try:
        cursor = db.execute(
            "INSERT INTO Comments (user_id, post_id, text_content, parent_comment_id) VALUES (?, ?, ?, ?)",
            (user_id, post_id, text_content, parent_comment_id)
        )
        db.commit()
        return cursor.lastrowid
    except sqlite3.Error as e:
        db.rollback()
        print(f"Error adding comment: {e}")
        return None

def get_comments_for_post(post_id):
    from app.models.community import Comment
    from app.models.user import User
    db = get_db()
    
    # Fetch all comments for the post
    rows = db.execute(
        """SELECT c.*, u.username, u.avatar_url
           FROM Comments c JOIN Users u ON c.user_id = u.id
           WHERE c.post_id = ? 
           ORDER BY c.created_at ASC""", # Important for threading logic later
        (post_id,)
    ).fetchall()

    comments_map = {} # To hold comments by their ID for easy lookup
    threaded_comments = [] # To hold top-level comments

    for row_data in rows:
        row = dict(row_data)
        user = User(id=row['user_id'], username=row['username'], email=None, password_hash=None, avatar_url=row['avatar_url'])
        comment = Comment(
            id=row['id'], user_id=row['user_id'], post_id=row['post_id'],
            text_content=row['text_content'], parent_comment_id=row['parent_comment_id'],
            created_at=row['created_at'], user=user, replies=[]
        )
        comments_map[comment.id] = comment

        if comment.parent_comment_id:
            if comment.parent_comment_id in comments_map:
                parent_comment = comments_map[comment.parent_comment_id]
                parent_comment.replies.append(comment)
        else:
            threaded_comments.append(comment)
            
    return threaded_comments # Returns a list of top-level comments, each with its replies nested

# WatchlistItem specific database functions
def add_or_update_watchlist_item(user_id, anime_id, status):
    from app.models.user_activity import WatchlistItem
    db = get_db()
    try:
        existing_item = db.execute(
            "SELECT id FROM WatchlistItems WHERE user_id = ? AND anime_id = ?",
            (user_id, anime_id)
        ).fetchone()

        if existing_item:
            # If status is the same, it's a no-op, or could be considered 'remove if same status clicked again'
            # For now, just update status and timestamp
            db.execute(
                "UPDATE WatchlistItems SET status = ?, added_at = CURRENT_TIMESTAMP WHERE id = ?",
                (status, existing_item['id'])
            )
            item_id = existing_item['id']
        else:
            cursor = db.execute(
                "INSERT INTO WatchlistItems (user_id, anime_id, status) VALUES (?, ?, ?)",
                (user_id, anime_id, status)
            )
            item_id = cursor.lastrowid
        db.commit()
        return item_id
    except sqlite3.Error as e:
        db.rollback()
        print(f"Error adding/updating watchlist item: {e}")
        return None

def remove_watchlist_item(user_id, anime_id): # Simplified: remove any status for this anime
    db = get_db()
    try:
        db.execute(
            "DELETE FROM WatchlistItems WHERE user_id = ? AND anime_id = ?",
            (user_id, anime_id)
        )
        db.commit()
        return True
    except sqlite3.Error as e:
        db.rollback()
        print(f"Error removing watchlist item: {e}")
        return False

def get_watchlist_for_user(user_id, status_filter=None):
    from app.models.user_activity import WatchlistItem
    from app.models.anime import Anime # To attach anime details
    db = get_db()
    
    query = """SELECT wi.id, wi.user_id, wi.anime_id, wi.status, wi.added_at,
                      a.title as anime_title, a.cover_image_url as anime_cover_image_url
               FROM WatchlistItems wi
               JOIN Anime a ON wi.anime_id = a.id
               WHERE wi.user_id = ?"""
    params = [user_id]

    if status_filter:
        query += " AND wi.status = ?"
        params.append(status_filter)
    
    query += " ORDER BY wi.added_at DESC"
    
    rows = db.execute(query, params).fetchall()
    
    items = []
    for row_data in rows:
        row = dict(row_data)
        anime_info = Anime(id=row['anime_id'], title=row['anime_title'], cover_image_url=row['anime_cover_image_url'])
        item = WatchlistItem(
            id=row['id'], user_id=row['user_id'], anime_id=row['anime_id'],
            status=row['status'], added_at=row['added_at'], anime=anime_info
        )
        items.append(item)
    return items

def get_watchlist_item_status(user_id, anime_id): # Renamed to avoid conflict with model name
    db = get_db()
    row = db.execute(
        "SELECT status FROM WatchlistItems WHERE user_id = ? AND anime_id = ?",
        (user_id, anime_id)
    ).fetchone()
    return row['status'] if row else None


# Notification specific database functions
def create_notification(user_id, type, content, link_url=None):
    from app.models.notifications import Notification
    db = get_db()
    try:
        cursor = db.execute(
            "INSERT INTO Notifications (user_id, type, content, link_url) VALUES (?, ?, ?, ?)",
            (user_id, type, content, link_url)
        )
        db.commit()
        return cursor.lastrowid
    except sqlite3.Error as e:
        db.rollback()
        print(f"Error creating notification: {e}")
        return None

def get_notifications_for_user(user_id, only_unread=False, limit=None):
    from app.models.notifications import Notification
    db = get_db()
    query = "SELECT * FROM Notifications WHERE user_id = ?"
    params = [user_id]

    if only_unread:
        query += " AND is_read = 0" # Assuming 0 for False
    
    query += " ORDER BY created_at DESC"

    if limit:
        query += " LIMIT ?"
        params.append(limit)
        
    rows = db.execute(query, params).fetchall()
    return [Notification(**row) for row in rows]

def count_unread_notifications(user_id):
    db = get_db()
    count = db.execute(
        "SELECT COUNT(id) FROM Notifications WHERE user_id = ? AND is_read = 0",
        (user_id,)
    ).fetchone()[0]
    return count

def mark_notification_as_read(notification_id, user_id):
    # user_id is to ensure a user can only mark their own notifications as read
    db = get_db()
    try:
        db.execute(
            "UPDATE Notifications SET is_read = 1 WHERE id = ? AND user_id = ?",
            (notification_id, user_id)
        )
        db.commit()
        return True
    except sqlite3.Error as e:
        db.rollback()
        print(f"Error marking notification as read: {e}")
        return False

def mark_all_notifications_as_read(user_id):
    db = get_db()
    try:
        db.execute("UPDATE Notifications SET is_read = 1 WHERE user_id = ?", (user_id,))
        db.commit()
        return True
    except sqlite3.Error as e:
        db.rollback()
        print(f"Error marking all notifications as read: {e}")
        return False


# Modify add_comment to generate notifications
def add_comment(user_id, post_id, text_content, parent_comment_id=None): # Original signature
    db = get_db()
    comment_id = None
    try:
        cursor = db.execute(
            "INSERT INTO Comments (user_id, post_id, text_content, parent_comment_id) VALUES (?, ?, ?, ?)",
            (user_id, post_id, text_content, parent_comment_id)
        )
        comment_id = cursor.lastrowid
        db.commit()
    except sqlite3.Error as e:
        db.rollback()
        print(f"Error adding comment: {e}")
        return None # Return None on failure

    if comment_id:
        # Notification logic
        try:
            post = get_post_by_id(post_id) # We need post title and author
            commenting_user = find_user_by_id(user_id) # User who made the current comment

            if not post or not commenting_user:
                print("Failed to fetch post or user details for notification.")
                return comment_id # Still return comment_id as comment was added

            link_url = url_for('community.post_detail', post_id=post_id, _external=True) + f"#comment-{comment_id}"

            # 1. Notify original post author (if not the one commenting)
            if post.user_id != user_id:
                content = f"{commenting_user.username} commented on your post: '{post.title}'"
                create_notification(post.user_id, 'post_reply', content, link_url)

            # 2. Notify parent comment author (if this is a reply and not to their own comment)
            if parent_comment_id:
                # Fetch the parent comment to get its author_id
                # Assuming a simple get_comment_by_id function that returns an object/dict with user_id
                parent_comment_row = db.execute("SELECT user_id FROM Comments WHERE id = ?", (parent_comment_id,)).fetchone()
                if parent_comment_row and parent_comment_row['user_id'] != user_id:
                    parent_comment_author_id = parent_comment_row['user_id']
                    # Fetch parent commenter's username for a more descriptive notification
                    # For simplicity, we'll use a generic message if we don't fetch parent commenter's name
                    content = f"{commenting_user.username} replied to your comment on the post: '{post.title}'"
                    create_notification(parent_comment_author_id, 'comment_reply', content, link_url)
        except Exception as e:
            # Log notification error but don't fail the comment operation
            print(f"Error creating notification for comment {comment_id}: {e}")
            
    return comment_id
