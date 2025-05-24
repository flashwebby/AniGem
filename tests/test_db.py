import pytest
from app.db import get_db, seed_db # seed_db might be tested via command too

def test_init_db_command(runner, app):
    """Test that the init-db command clears existing data and creates new tables."""
    # If there was data, it should be cleared.
    # For a more robust test, you could add some dummy data, run init-db, then check if it's gone.
    # However, the command itself prints "Initialized the database." on success.
    result = runner.invoke(args=['init-db'])
    assert 'Initialized the database.' in result.output
    
    # Check if tables were created (e.g., Users table)
    with app.app_context():
        db = get_db()
        # This query will fail if tables don't exist
        try:
            db.execute("SELECT id FROM Users LIMIT 1").fetchall()
            db.execute("SELECT id FROM Anime LIMIT 1").fetchall()
            # Add more table checks if necessary
            assert True # If queries above don't raise an exception, tables exist
        except Exception as e:
            pytest.fail(f"Database tables not created properly by init-db: {e}")

def test_seed_db_command(runner, app):
    """Test that the seed-db command populates the database with sample data."""
    # init-db is called by seed-db command in db.py, so tables should be fresh
    result = runner.invoke(args=['seed-db'])
    assert 'Database seeded.' in result.output
    assert 'Seeding the database...' in result.output # Check for intermediate message

    # Verify that some sample data exists
    with app.app_context():
        db = get_db()
        # Check for sample genres (defined in db.py seed_db function)
        action_genre = db.execute("SELECT id FROM Genres WHERE name = 'Action'").fetchone()
        assert action_genre is not None, "Action genre not found after seeding."

        # Check for sample anime (defined in db.py seed_db function)
        code_geass = db.execute("SELECT id FROM Anime WHERE title = 'Code Geass: Lelouch of the Rebellion'").fetchone()
        assert code_geass is not None, "Code Geass not found after seeding."
        
        # Check if anime is linked to genres
        code_geass_genres = db.execute(
            "SELECT g.name FROM Genres g JOIN AnimeGenres ag ON g.id = ag.genre_id WHERE ag.anime_id = ?",
            (code_geass['id'],)
        ).fetchall()
        assert len(code_geass_genres) > 0, "Code Geass should have genres linked."
        genre_names = [g['name'] for g in code_geass_genres]
        assert "Action" in genre_names
        assert "Sci-Fi" in genre_names

        # Check if average ratings were initialized (should be 0.0 if no actual ratings)
        # This assumes update_anime_average_rating sets to 0 if no ratings exist
        cg_rating = db.execute("SELECT average_rating FROM Anime WHERE id = ?", (code_geass['id'],)).fetchone()
        assert cg_rating is not None and cg_rating['average_rating'] == 0.0, "Initial average rating should be 0.0"


def test_seed_db_function_directly(app):
    """Test the seed_db Python function directly if needed for more granular checks."""
    with app.app_context():
        init_db() # Start with a clean schema
        seed_db() # Call the Python function

        db = get_db()
        action_genre = db.execute("SELECT id FROM Genres WHERE name = 'Action'").fetchone()
        assert action_genre is not None

        k_on_anime = db.execute("SELECT id FROM Anime WHERE title = 'K-On!'").fetchone()
        assert k_on_anime is not None
        k_on_genres = db.execute(
            "SELECT g.name FROM Genres g JOIN AnimeGenres ag ON g.id = ag.genre_id WHERE ag.anime_id = ?",
            (k_on_anime['id'],)
        ).fetchall()
        genre_names = [g['name'] for g in k_on_genres]
        assert "Slice of Life" in genre_names
        assert "Comedy" in genre_names

        k_on_tags = db.execute(
            "SELECT t.name FROM Tags t JOIN AnimeTags at ON t.id = at.tag_id WHERE at.anime_id = ?",
            (k_on_anime['id'],)
        ).fetchall()
        tag_names = [t['name'] for t in k_on_tags]
        assert "School Life" in tag_names
    
    # Further checks can be added for other seeded data.
