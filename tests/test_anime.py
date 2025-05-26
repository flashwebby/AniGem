import pytest
from flask import url_for
from app.db import get_anime_by_id, get_all_anime, get_random_anime, get_db

def test_list_anime_page(client, seeded_database):
    """Test the main anime listing page."""
    response = client.get(url_for('anime.list_anime'))
    assert response.status_code == 200
    # Check for some seeded anime titles in the response
    assert b"Code Geass: Lelouch of the Rebellion" in response.data
    assert b"Attack on Titan" in response.data
    assert b"K-On!" in response.data
    # Check for filter form elements
    assert b'<form method="get" action="/anime/">' in response.data
    assert b'Genre:' in response.data
    assert b'Tag:' in response.data # Assuming tags are part of filters

def test_anime_detail_page(client, seeded_database, app):
    """Test the anime detail page for a specific anime."""
    with app.app_context(): # Need app context to query DB for an ID
        # Get a known anime ID from seeded data
        code_geass = get_db().execute("SELECT id FROM Anime WHERE title = 'Code Geass: Lelouch of the Rebellion'").fetchone()
        assert code_geass is not None, "Code Geass not found in seeded data for test setup."
        anime_id = code_geass['id']

    response = client.get(url_for('anime.detail', anime_id=anime_id))
    assert response.status_code == 200
    assert b"Code Geass: Lelouch of the Rebellion" in response.data
    assert b"Synopsis" in response.data # Assuming description becomes Synopsis
    assert b"Genres:" in response.data
    assert b"Action" in response.data # Check for one of its genres
    assert b"Mecha" in response.data # Check for one of its tags

    # Test for non-existent anime
    response_non_existent = client.get(url_for('anime.detail', anime_id=9999))
    assert response_non_existent.status_code == 302 # Redirects
    assert response_non_existent.headers['Location'] == url_for('anime.list_anime')
    # Check for flash message after redirect
    # To check flash messages, you need to make a request that would display them,
    # or inspect the session if the flash message is set before redirect.
    # For simplicity, we'll assume the redirect implies an error was handled.
    # More advanced: client.get(url_for('anime.detail', anime_id=9999), follow_redirects=True)
    # and check the content of the list page for the flash message.


def test_anime_filtering(client, seeded_database, app):
    """Test filtering anime by genre, year, language."""
    with app.app_context():
        # Get IDs for known genre, tag, year, language from seeded data
        action_genre_id = get_db().execute("SELECT id FROM Genres WHERE name = 'Action'").fetchone()['id']
        mecha_tag_id = get_db().execute("SELECT id FROM Tags WHERE name = 'Mecha'").fetchone()['id']
        
        # Filter by Genre: Action
        response_genre = client.get(url_for('anime.list_anime', genre_id=action_genre_id))
        assert response_genre.status_code == 200
        assert b"Code Geass" in response_genre.data
        assert b"Attack on Titan" in response_genre.data
        assert b"K-On!" not in response_genre.data # K-On! is Slice of Life/Comedy

        # Filter by Tag: Mecha
        response_tag = client.get(url_for('anime.list_anime', tag_id=mecha_tag_id))
        assert response_tag.status_code == 200
        assert b"Code Geass" in response_tag.data
        assert b"Attack on Titan" not in response_tag.data # AOT is not Mecha

        # Filter by Year: 2009 (K-On!)
        response_year = client.get(url_for('anime.list_anime', release_year=2009))
        assert response_year.status_code == 200
        assert b"K-On!" in response_year.data
        assert b"Code Geass" not in response_year.data

        # Filter by Language: Japanese (all seeded anime are Japanese)
        # Assuming 'Japanese' is a valid language string in the DB
        response_lang = client.get(url_for('anime.list_anime', language='Japanese'))
        assert response_lang.status_code == 200
        assert b"Code Geass" in response_lang.data
        assert b"K-On!" in response_lang.data
        
        # Filter by multiple: Genre Action AND Year 2013 (Attack on Titan)
        response_multi = client.get(url_for('anime.list_anime', genre_id=action_genre_id, release_year=2013))
        assert response_multi.status_code == 200
        assert b"Attack on Titan" in response_multi.data
        assert b"Code Geass" not in response_multi.data # Code Geass is not 2013
        assert b"K-On!" not in response_multi.data # K-On! is not Action

def test_surprise_me_feature(client, seeded_database, app):
    """Test the 'Surprise Me' feature."""
    # Ensure there's at least one anime for surprise me to work
    with app.app_context():
        assert get_db().execute("SELECT COUNT(id) FROM Anime").fetchone()[0] > 0

    response = client.get(url_for('anime.surprise_me'))
    assert response.status_code == 302 # Redirects to an anime detail page
    
    # Check that the redirect location is a valid anime detail URL
    redirect_location = response.headers['Location']
    assert redirect_location.startswith('/anime/')
    
    try:
        anime_id_str = redirect_location.split('/anime/')[1]
        anime_id = int(anime_id_str)
        
        # Verify the redirected anime ID exists
        with app.app_context():
            anime = get_anime_by_id(anime_id)
            assert anime is not None
            
        # Follow the redirect and check if the page loads correctly
        response_followed = client.get(redirect_location)
        assert response_followed.status_code == 200
        assert anime.title.encode() in response_followed.data # Check for the title of the random anime

    except (IndexError, ValueError):
        pytest.fail(f"Surprise Me feature redirected to an invalid URL: {redirect_location}")


# Direct DB function tests (optional, if complex logic not covered by route tests)
# These are examples; often, testing through routes/client is preferred (integration style).
def test_db_get_all_anime(app, seeded_database):
    with app.app_context():
        all_anime = get_all_anime()
        assert len(all_anime) >= 4 # Based on seeded data
        titles = [a.title for a in all_anime]
        assert "Code Geass: Lelouch of the Rebellion" in titles
        assert "K-On!" in titles

def test_db_get_anime_by_id(app, seeded_database):
     with app.app_context():
        # Find K-On! ID
        k_on_db = get_db().execute("SELECT id FROM Anime WHERE title = 'K-On!'").fetchone()
        assert k_on_db is not None
        k_on_id = k_on_db['id']
        
        anime = get_anime_by_id(k_on_id)
        assert anime is not None
        assert anime.title == "K-On!"
        assert anime.release_year == 2009
        assert len(anime.genres) > 0
        assert any(g.name == "Slice of Life" for g in anime.genres)
        assert len(anime.tags) > 0
        assert any(t.name == "School Life" for t in anime.tags)

def test_db_get_random_anime(app, seeded_database):
    with app.app_context():
        random_anime = get_random_anime()
        assert random_anime is not None
        assert hasattr(random_anime, 'title')
        # Ensure it's one of the known anime
        all_titles = [a.title for a in get_all_anime()]
        assert random_anime.title in all_titles

# Add test for add_anime page if it's implemented (currently commented out in routes)
# def test_add_anime_page_get(client_user1): # Assuming admin/logged-in user
#     response = client_user1.get(url_for('anime.add_anime_route'))
#     assert response.status_code == 200 # Or 403 if not admin
#     assert b"Add New Anime" in response.data

# def test_add_anime_post(client_user1, app): # Assuming admin/logged-in user
#     # ... data for new anime ...
#     response = client_user1.post(url_for('anime.add_anime_route'), data=new_anime_data, follow_redirects=True)
#     assert response.status_code == 200
#     # ... check for success message and if anime is in DB ...
#     with app.app_context():
#         newly_added = get_db().execute("SELECT * FROM Anime WHERE title = ?", (new_anime_data['title'],)).fetchone()
#         assert newly_added is not None
#         # ... check genres and tags ...
```
