from flask import Blueprint, render_template, request, redirect, url_for, flash, g
from app.db import (
    get_all_anime, get_anime_by_id, get_random_anime, 
    get_all_genres, get_all_tags, get_genre_by_id, get_tag_by_id,
    get_reviews_for_anime, get_user_rating_for_anime, get_user_vote_for_review,
    get_watchlist_item_status # Added for watchlist status on anime detail page
)
from app.routes.auth import login_required

bp = Blueprint('anime', __name__, url_prefix='/anime')

@bp.route('/')
def list_anime():
    # Get filter parameters from request.args
    selected_genre_id = request.args.get('genre_id', type=int)
    selected_tag_id = request.args.get('tag_id', type=int)
    release_year = request.args.get('release_year', type=int)
    language = request.args.get('language')

    filters = {}
    if selected_genre_id:
        filters['genre_id'] = selected_genre_id
    if selected_tag_id:
        filters['tag_id'] = selected_tag_id
    if release_year:
        filters['release_year'] = release_year
    if language and language != "all": # Assuming "all" means no filter
        filters['language'] = language
    
    all_anime = get_all_anime(filters=filters if filters else None)
    all_genres = get_all_genres()
    all_tags = get_all_tags()
    
    # This is just an example, you might want to get unique years/languages from your DB
    # For simplicity, I'm not dynamically generating these from the current anime list in the DB
    available_years = sorted(list(set(a.release_year for a in get_all_anime() if a.release_year)), reverse=True)
    available_languages = sorted(list(set(a.language for a in get_all_anime() if a.language)))


    return render_template(
        'anime/list.html', 
        anime_list=all_anime, 
        genres=all_genres, 
        tags=all_tags,
        available_years=available_years,
        available_languages=available_languages,
        selected_genre_id=selected_genre_id,
        selected_tag_id=selected_tag_id,
        selected_year=release_year,
        selected_language=language
    )

@bp.route('/<int:anime_id>')
def detail(anime_id):
    anime = get_anime_by_id(anime_id)
    if anime is None:
        flash('Anime not found.', 'error')
        return redirect(url_for('anime.list_anime'))

    reviews = get_reviews_for_anime(anime_id)
    current_user_rating = None
    user_votes = {} # To store user's vote for each review: {review_id: 'upvote'/'downvote'}
    current_watchlist_status = None # For watchlist

    if g.user:
        current_user_rating = get_user_rating_for_anime(g.user.id, anime_id)
        current_watchlist_status = get_watchlist_item_status(g.user.id, anime_id) # Get watchlist status
        for review_item in reviews: # Changed variable name from review to review_item
            user_vote = get_user_vote_for_review(g.user.id, review_item.id)
            if user_vote:
                user_votes[review_item.id] = user_vote
                
    return render_template(
        'anime/detail.html', 
        anime=anime, 
        reviews=reviews, 
        current_user_rating=current_user_rating,
        user_votes=user_votes,
        current_watchlist_status=current_watchlist_status # Pass to template
    )

@bp.route('/surprise')
def surprise_me():
    anime = get_random_anime()
    if anime is None:
        flash('No anime available to surprise you with!', 'error')
        return redirect(url_for('anime.list_anime'))
    return redirect(url_for('anime.detail', anime_id=anime.id))

# Optional: Add Anime Page (Basic Structure)
# @bp.route('/add', methods=('GET', 'POST'))
# @login_required # Make sure user is logged in
def add_anime_route(): # Renamed to avoid conflict with db.add_anime
    # # Check if user has admin privileges if you implement roles
    # if not g.user.is_admin: # Assuming an 'is_admin' attribute on User model
    #     flash("You don't have permission to add anime.", "error")
    #     return redirect(url_for('anime.list_anime'))

    # if request.method == 'POST':
    #     title = request.form['title']
    #     description = request.form.get('description')
    #     release_year = request.form.get('release_year', type=int)
    #     cover_image_url = request.form.get('cover_image_url')
    #     language = request.form.get('language')
    #     genre_names = request.form.getlist('genres') # Assuming multi-select for genres
    #     tag_names = request.form.getlist('tags')     # Assuming multi-select for tags
        
    #     error = None
    #     if not title:
    #         error = "Title is required."
        
    #     if error is None:
    #         from app.db import add_anime as db_add_anime # Alias to avoid name clash
    #         anime_id = db_add_anime(title, description, release_year, cover_image_url, language, genre_names, tag_names)
    #         if anime_id:
    #             flash(f"Anime '{title}' added successfully!", "success")
    #             return redirect(url_for('anime.detail', anime_id=anime_id))
    #         else:
    #             error = "Failed to add anime. Check logs for details."
        
    #     if error:
    #         flash(error, "error")
            
    # all_genres = get_all_genres()
    # all_tags = get_all_tags()
    # return render_template('anime/add.html', genres=all_genres, tags=all_tags)
    pass # For now, the add anime route is not fully implemented.

# Example of how to register this blueprint in app/__init__.py:
# from .routes import anime # Add this line in create_app
# app.register_blueprint(anime.bp) # Add this line in create_app
