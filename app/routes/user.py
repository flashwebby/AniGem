from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from app.db import (
    find_user_by_username, get_watchlist_for_user, 
    get_friendship_status # Added for profile page friend actions
)
from app.routes.auth import login_required # Import the login_required decorator

bp = Blueprint('user', __name__, url_prefix='/user')

@bp.route('/profile/<username>')
@login_required # Protect this route
def profile(username):
    # Public profiles could be a future enhancement.
    # For now, allow viewing other profiles, but actions are context-dependent.
    user_profile_data = find_user_by_username(username)
    if not user_profile_data:
        flash("User profile not found.", "error")
        return redirect(url_for('hello'))

    friendship_status_with_viewer = None
    is_own_profile = False

    if g.user:
        is_own_profile = (g.user.id == user_profile_data.id)
        if not is_own_profile:
            friendship_status_with_viewer = get_friendship_status(g.user.id, user_profile_data.id)
    
    # Fetch watchlist for the user whose profile is being viewed
    watchlist_items = get_watchlist_for_user(user_profile_data.id)
    watchlists = {
        'plan_to_watch': [],
        'watching': [],
        'completed': [],
        'dropped': [],
        'bookmarked': []
    }
    for item in watchlist_items:
        if item.status in watchlists:
            watchlists[item.status].append(item)
            
    return render_template('user/profile.html', 
                           user_profile=user_profile_data, 
                           watchlists=watchlists,
                           is_own_profile=is_own_profile,
                           friendship_status_with_viewer=friendship_status_with_viewer)

    # Old logic for restricting to own profile:
    # if g.user and g.user.username == username:
    #     user_profile_data = find_user_by_username(username) # Fetch full user data if g.user is minimal
    #     if not user_profile_data:
    #         flash("User profile not found.", "error")
            return redirect(url_for('hello')) # Redirect to home or a generic error page

        # Fetch watchlist for the user
        # Group watchlist items by status for easier display
        watchlist_items = get_watchlist_for_user(user_profile_data.id)
        watchlists = {
            'plan_to_watch': [],
            'watching': [],
            'completed': [],
            'dropped': [],
            'bookmarked': []
        }
        for item in watchlist_items:
            if item.status in watchlists:
                watchlists[item.status].append(item)
            
        # return render_template('user/profile.html', user_profile=user_profile_data, watchlists=watchlists)
    # else:
    #     # If trying to access another user's profile or not logged in appropriately
    #     flash("You can only view your own profile.", "error")
    #     return redirect(url_for('user.profile', username=g.user.username if g.user else '')) # Redirect to own profile or login

# Example of how to register this blueprint in app/__init__.py:
# from .routes import user # Add this line in create_app
# app.register_blueprint(user.bp) # Add this line in create_app
