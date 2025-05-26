from flask import Blueprint, request, redirect, url_for, flash, g, jsonify
from app.db import (
    add_or_update_rating, add_review, add_or_update_review_vote,
    get_user_rating_for_anime, get_anime_by_id, get_review_by_id # Assuming get_review_by_id exists
)
from app.routes.auth import login_required

bp = Blueprint('ratings_reviews', __name__)

# Helper function to get review by id (if not already in db.py)
# This is a placeholder, ensure it's properly implemented in db.py or here if only used locally.
def get_review_by_id_local(review_id):
    # This function should ideally be in db.py for consistency
    from app.db import get_db
    db = get_db()
    row = db.execute("SELECT * FROM Reviews WHERE id = ?", (review_id,)).fetchone()
    # This is a simplified return, actual Review model construction might be needed
    return dict(row) if row else None


@bp.route('/anime/<int:anime_id>/rate', methods=['POST'])
@login_required
def rate_anime(anime_id):
    score = request.form.get('score', type=int)
    if score is None or not (1 <= score <= 10):
        flash('Invalid score. Please select a score between 1 and 10.', 'error')
        return redirect(url_for('anime.detail', anime_id=anime_id))

    if get_anime_by_id(anime_id) is None: # Check if anime exists
        flash('Anime not found.', 'error')
        return redirect(url_for('anime.list_anime'))

    rating_id = add_or_update_rating(g.user.id, anime_id, score)
    if rating_id:
        flash('Your rating has been submitted successfully!', 'success')
    else:
        flash('Failed to submit your rating.', 'error')
    
    return redirect(url_for('anime.detail', anime_id=anime_id))

@bp.route('/anime/<int:anime_id>/review', methods=['POST'])
@login_required
def review_anime(anime_id):
    text_content = request.form.get('text_content')
    is_spoiler = 'is_spoiler' in request.form
    
    if not text_content:
        flash('Review text cannot be empty.', 'error')
        return redirect(url_for('anime.detail', anime_id=anime_id))

    if get_anime_by_id(anime_id) is None: # Check if anime exists
        flash('Anime not found.', 'error')
        return redirect(url_for('anime.list_anime'))

    # Optional: Link review to user's existing rating if they have one
    user_rating = get_user_rating_for_anime(g.user.id, anime_id)
    rating_id = user_rating.id if user_rating else None
    
    review_id = add_review(g.user.id, anime_id, text_content, rating_id, is_spoiler)
    if review_id:
        flash('Your review has been posted successfully!', 'success')
    else:
        flash('Failed to post your review.', 'error')
        
    return redirect(url_for('anime.detail', anime_id=anime_id))

@bp.route('/review/<int:review_id>/vote', methods=['POST'])
@login_required
def vote_review(review_id):
    vote_type = request.form.get('vote_type') # 'upvote' or 'downvote'
    
    if vote_type not in ['upvote', 'downvote']:
        flash('Invalid vote type.', 'error')
        # Attempt to find the anime_id associated with the review to redirect back
        # This might need a more robust way to get the anime_id if get_review_by_id_local is too simple
        review_details = get_review_by_id_local(review_id) 
        if review_details:
            return redirect(url_for('anime.detail', anime_id=review_details['anime_id']))
        else: # Fallback if anime_id can't be determined
            return redirect(url_for('anime.list_anime'))


    if add_or_update_review_vote(g.user.id, review_id, vote_type):
        flash('Your vote has been recorded.', 'success')
    else:
        flash('Failed to record your vote.', 'error')

    # Redirect back to the anime detail page where the review is displayed
    # This requires fetching the anime_id associated with the review_id
    # For now, assuming get_review_by_id_local or a similar function in db.py can provide anime_id
    review_details = get_review_by_id_local(review_id) # Placeholder
    if review_details:
        return redirect(url_for('anime.detail', anime_id=review_details['anime_id']))
    else:
        # Fallback if anime_id can't be determined, maybe to user's profile or home
        flash('Could not redirect back to anime page, review not found.', 'error')
        return redirect(url_for('hello')) # 'hello' is the placeholder for home route

# Example of how to register this blueprint in app/__init__.py:
# from .routes import ratings_reviews
# app.register_blueprint(ratings_reviews.bp)
