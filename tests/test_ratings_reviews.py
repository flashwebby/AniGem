import pytest
from flask import url_for, g
from app.db import get_db, get_anime_by_id, get_user_rating_for_anime, get_reviews_for_anime, get_user_vote_for_review

# Helper to get an anime ID (e.g., Code Geass)
def get_seeded_anime_id(app, title="Code Geass: Lelouch of the Rebellion"):
    with app.app_context():
        anime = get_db().execute("SELECT id FROM Anime WHERE title = ?", (title,)).fetchone()
        assert anime is not None, f"Anime '{title}' not found in seeded data."
        return anime['id']

# Helper to get a review ID for a user and anime
def get_review_id(app, user_id, anime_id):
    with app.app_context():
        review = get_db().execute(
            "SELECT id FROM Reviews WHERE user_id = ? AND anime_id = ? ORDER BY created_at DESC LIMIT 1",
            (user_id, anime_id)
        ).fetchone()
        return review['id'] if review else None

def test_rate_anime(client_user1, app, seeded_database, user1_data):
    anime_id = get_seeded_anime_id(app)
    
    # Test submitting a new rating
    response = client_user1.post(url_for('ratings_reviews.rate_anime', anime_id=anime_id), data={'score': '8'})
    assert response.status_code == 302 # Redirects to anime detail page
    assert response.headers['Location'] == url_for('anime.detail', anime_id=anime_id)

    with app.app_context():
        user_id = get_db().execute("SELECT id FROM Users WHERE username = ?", (user1_data['username'],)).fetchone()['id']
        rating = get_user_rating_for_anime(user_id, anime_id)
        assert rating is not None
        assert rating.score == 8
        
        # Check if anime's average rating was updated
        anime = get_anime_by_id(anime_id)
        assert anime.average_rating == 8.0 # Only one rating so far

    # Test updating the rating
    client_user1.post(url_for('ratings_reviews.rate_anime', anime_id=anime_id), data={'score': '9'})
    with app.app_context():
        rating = get_user_rating_for_anime(user_id, anime_id)
        assert rating.score == 9
        anime = get_anime_by_id(anime_id)
        assert anime.average_rating == 9.0

    # Test invalid score
    response_invalid = client_user1.post(url_for('ratings_reviews.rate_anime', anime_id=anime_id), data={'score': '11'})
    # Should redirect and flash error
    assert response_invalid.status_code == 302
    # To check flash, follow redirect and check content
    response_invalid_followed = client_user1.post(url_for('ratings_reviews.rate_anime', anime_id=anime_id), data={'score': '11'}, follow_redirects=True)
    assert b"Invalid score" in response_invalid_followed.data


def test_review_anime(client_user1, app, seeded_database, user1_data):
    anime_id = get_seeded_anime_id(app)
    user_id = get_user_id(app, user1_data['username'])

    # Test submitting a new review
    review_text = "This is a great anime!"
    response = client_user1.post(
        url_for('ratings_reviews.review_anime', anime_id=anime_id),
        data={'text_content': review_text, 'is_spoiler': 'y'} # 'y' for checkbox
    )
    assert response.status_code == 302 # Redirects
    
    with app.app_context():
        reviews = get_reviews_for_anime(anime_id)
        assert len(reviews) > 0
        my_review = next((r for r in reviews if r.user_id == user_id and r.text_content == review_text), None)
        assert my_review is not None
        assert my_review.is_spoiler is True # In SQLite, boolean might be 1

    # Test submitting an empty review
    response_empty = client_user1.post(
        url_for('ratings_reviews.review_anime', anime_id=anime_id),
        data={'text_content': ''},
        follow_redirects=True
    )
    assert b"Review text cannot be empty" in response_empty.data

def test_vote_review(client_user1, client_user2, app, seeded_database, user1_data, user2_data):
    anime_id = get_seeded_anime_id(app)
    user1_id = get_user_id(app, user1_data['username'])
    user2_id = get_user_id(app, user2_data['username'])

    # User1 posts a review
    client_user1.post(url_for('ratings_reviews.review_anime', anime_id=anime_id), data={'text_content': 'User 1 review'})
    review_id = get_review_id(app, user1_id, anime_id)
    assert review_id is not None

    # User2 upvotes User1's review
    response_upvote = client_user2.post(url_for('ratings_reviews.vote_review', review_id=review_id), data={'vote_type': 'upvote'})
    assert response_upvote.status_code == 302 # Redirects
    
    with app.app_context():
        review = get_db().execute("SELECT upvotes, downvotes FROM Reviews WHERE id = ?", (review_id,)).fetchone()
        assert review['upvotes'] == 1
        assert review['downvotes'] == 0
        assert get_user_vote_for_review(user2_id, review_id) == 'upvote'

    # User2 changes vote to downvote
    client_user2.post(url_for('ratings_reviews.vote_review', review_id=review_id), data={'vote_type': 'downvote'})
    with app.app_context():
        review = get_db().execute("SELECT upvotes, downvotes FROM Reviews WHERE id = ?", (review_id,)).fetchone()
        assert review['upvotes'] == 0
        assert review['downvotes'] == 1
        assert get_user_vote_for_review(user2_id, review_id) == 'downvote'

    # User2 removes their downvote (clicks downvote again)
    client_user2.post(url_for('ratings_reviews.vote_review', review_id=review_id), data={'vote_type': 'downvote'})
    with app.app_context():
        review = get_db().execute("SELECT upvotes, downvotes FROM Reviews WHERE id = ?", (review_id,)).fetchone()
        assert review['upvotes'] == 0
        assert review['downvotes'] == 0
        assert get_user_vote_for_review(user2_id, review_id) is None

    # User1 (author) cannot vote for their own review (optional check, depends on requirements, not explicitly implemented)
    # For now, we assume this is allowed or not checked.

    # Test invalid vote type
    response_invalid_vote = client_user2.post(
        url_for('ratings_reviews.vote_review', review_id=review_id), 
        data={'vote_type': 'sideways'},
        follow_redirects=True
    )
    assert b"Invalid vote type" in response_invalid_vote.data


def test_average_rating_calculation(client_user1, client_user2, app, seeded_database, user1_data, user2_data):
    anime_id = get_seeded_anime_id(app, title="K-On!") # Use a different anime for this test
    
    # User1 rates 7
    client_user1.post(url_for('ratings_reviews.rate_anime', anime_id=anime_id), data={'score': '7'})
    with app.app_context():
        anime = get_anime_by_id(anime_id)
        assert anime.average_rating == 7.0

    # User2 rates 9
    client_user2.post(url_for('ratings_reviews.rate_anime', anime_id=anime_id), data={'score': '9'})
    with app.app_context():
        anime = get_anime_by_id(anime_id)
        assert anime.average_rating == 8.0 # (7+9)/2

    # User1 updates rating to 5
    client_user1.post(url_for('ratings_reviews.rate_anime', anime_id=anime_id), data={'score': '5'})
    with app.app_context():
        anime = get_anime_by_id(anime_id)
        assert anime.average_rating == 7.0 # (5+9)/2

# Test that review appears on anime detail page
def test_review_display_on_anime_page(client, client_user1, app, seeded_database, user1_data):
    anime_id = get_seeded_anime_id(app)
    review_text = "My awesome review for display."
    
    # User1 posts a review
    client_user1.post(
        url_for('ratings_reviews.review_anime', anime_id=anime_id),
        data={'text_content': review_text, 'is_spoiler': 'n'} # Not a spoiler
    )
    
    # View the anime detail page (as anonymous client)
    response = client.get(url_for('anime.detail', anime_id=anime_id))
    assert response.status_code == 200
    assert review_text.encode() in response.data
    assert user1_data['username'].encode() in response.data # Check reviewer's username is there

    # Test spoiler
    spoiler_text = "This is a major spoiler!"
    client_user1.post(
        url_for('ratings_reviews.review_anime', anime_id=anime_id),
        data={'text_content': spoiler_text, 'is_spoiler': 'y'}
    )
    response_spoiler = client.get(url_for('anime.detail', anime_id=anime_id))
    assert spoiler_text.encode() in response_spoiler.data # Content should be there but hidden by JS
    assert b"Reveal Spoiler" in response_spoiler.data # Button to reveal spoiler

# Test rating linked to review
def test_review_with_rating_link(client_user1, app, seeded_database, user1_data):
    anime_id = get_seeded_anime_id(app)
    user_id = get_user_id(app, user1_data['username'])

    # User1 rates the anime
    client_user1.post(url_for('ratings_reviews.rate_anime', anime_id=anime_id), data={'score': '8'})
    
    # User1 then reviews the anime
    review_text = "Review linked to my 8/10 rating."
    client_user1.post(
        url_for('ratings_reviews.review_anime', anime_id=anime_id),
        data={'text_content': review_text}
    )

    with app.app_context():
        reviews = get_reviews_for_anime(anime_id)
        my_review = next((r for r in reviews if r.user_id == user_id and r.text_content == review_text), None)
        assert my_review is not None
        assert my_review.rating_id is not None
        
        rating = get_db().execute("SELECT score FROM Ratings WHERE id = ?", (my_review.rating_id,)).fetchone()
        assert rating is not None
        assert rating['score'] == 8

        # Also check this on the detail page display
        response = client_user1.get(url_for('anime.detail', anime_id=anime_id))
        assert review_text.encode() in response.data
        assert b"(Rated: 8/10)" in response.data # Check how it's displayed
```
