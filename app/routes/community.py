from flask import Blueprint, render_template, request, redirect, url_for, flash, g, jsonify
from app.db import (
    get_all_subcommunities, add_subcommunity, get_subcommunity_by_id, get_subcommunity_by_name,
    add_post, get_post_by_id, get_posts_for_subcommunity, get_all_posts,
    add_or_update_post_vote, get_user_vote_for_post,
    add_comment, get_comments_for_post
)
from app.routes.auth import login_required

bp = Blueprint('community', __name__, url_prefix='/community')

@bp.route('/')
def home():
    subcommunities = get_all_subcommunities()
    # For "Recent Posts", get_all_posts already sorts by created_at DESC
    recent_posts = get_all_posts(limit=10) # Get top 10 recent posts from all communities
    return render_template('community/home.html', subcommunities=subcommunities, recent_posts=recent_posts)

@bp.route('/s/<subcommunity_identifier>') # Can be ID or name
def subcommunity_detail(subcommunity_identifier):
    subcommunity = None
    try:
        # Try to convert to int, if it works, it's an ID
        sub_id = int(subcommunity_identifier)
        subcommunity = get_subcommunity_by_id(sub_id)
    except ValueError:
        # If not an int, it's a name
        subcommunity = get_subcommunity_by_name(subcommunity_identifier)

    if not subcommunity:
        flash('Subcommunity not found.', 'error')
        return redirect(url_for('community.home'))
    
    posts = get_posts_for_subcommunity(subcommunity.id)
    return render_template('community/subcommunity_detail.html', subcommunity=subcommunity, posts=posts)

@bp.route('/post/<int:post_id>')
def post_detail(post_id):
    post = get_post_by_id(post_id)
    if not post:
        flash('Post not found.', 'error')
        return redirect(url_for('community.home'))
    
    comments = get_comments_for_post(post_id) # This should fetch threaded comments
    user_vote = None
    if g.user:
        user_vote = get_user_vote_for_post(g.user.id, post_id)
        
    return render_template('community/post_detail.html', post=post, comments=comments, user_vote=user_vote)

@bp.route('/create_post', methods=('GET', 'POST'))
@bp.route('/s/<int:subcommunity_id>/submit', methods=('GET', 'POST'))
@login_required
def create_post(subcommunity_id=None):
    subcommunities = get_all_subcommunities() # For dropdown if creating a general post
    target_subcommunity = None
    if subcommunity_id:
        target_subcommunity = get_subcommunity_by_id(subcommunity_id)
        if not target_subcommunity:
            flash("Subcommunity not found.", "error")
            return redirect(url_for('community.home'))

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        post_type = request.form.get('post_type', 'discussion')
        
        # Determine subcommunity_id from either URL or form
        form_subcommunity_id = request.form.get('subcommunity_id', type=int)
        final_subcommunity_id = subcommunity_id if subcommunity_id else form_subcommunity_id

        if not title:
            flash('Title is required.', 'error')
        else:
            post_id = add_post(g.user.id, title, content, final_subcommunity_id, post_type)
            if post_id:
                flash('Post created successfully!', 'success')
                return redirect(url_for('community.post_detail', post_id=post_id))
            else:
                flash('Failed to create post.', 'error')
    
    return render_template('community/create_post.html', subcommunities=subcommunities, target_subcommunity=target_subcommunity)

@bp.route('/create_subcommunity', methods=('GET', 'POST'))
@login_required # Or admin_required if you implement roles
def create_subcommunity():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form.get('description', '')

        if not name:
            flash('Subcommunity name is required.', 'error')
        else:
            # Ensure name uniqueness (db level or check here)
            if get_subcommunity_by_name(name):
                flash(f"Subcommunity with name '{name}' already exists.", 'error')
            else:
                sub = add_subcommunity(name, description, g.user.id)
                if sub:
                    flash(f"Subcommunity '{name}' created successfully!", 'success')
                    return redirect(url_for('community.subcommunity_detail', subcommunity_identifier=sub.id))
                else:
                    flash('Failed to create subcommunity.', 'error')
    return render_template('community/create_subcommunity.html')


@bp.route('/post/<int:post_id>/vote', methods=['POST'])
@login_required
def vote_post(post_id):
    vote_type = request.form.get('vote_type')
    if vote_type not in ['upvote', 'downvote']:
        return jsonify({'success': False, 'message': 'Invalid vote type.'}), 400

    if not get_post_by_id(post_id): # Check if post exists
        return jsonify({'success': False, 'message': 'Post not found.'}), 404

    if add_or_update_post_vote(g.user.id, post_id, vote_type):
        post = get_post_by_id(post_id) # Fetch updated vote counts
        return jsonify({
            'success': True, 
            'message': 'Vote recorded.', 
            'upvotes': post.upvotes, 
            'downvotes': post.downvotes,
            'new_vote_status': get_user_vote_for_post(g.user.id, post_id) # send back the new status
        })
    else:
        return jsonify({'success': False, 'message': 'Failed to record vote.'}), 500

@bp.route('/post/<int:post_id>/comment', methods=['POST'])
@login_required
def comment_on_post(post_id):
    text_content = request.form.get('text_content')
    parent_comment_id = request.form.get('parent_comment_id', type=int) # For replies

    if not text_content:
        flash('Comment text cannot be empty.', 'error')
        return redirect(url_for('community.post_detail', post_id=post_id))

    if not get_post_by_id(post_id): # Check if post exists
        flash('Post not found.', 'error')
        return redirect(url_for('community.home'))

    comment_id = add_comment(g.user.id, post_id, text_content, parent_comment_id)
    if comment_id:
        flash('Comment posted successfully!', 'success')
    else:
        flash('Failed to post comment.', 'error')
    
    return redirect(url_for('community.post_detail', post_id=post_id))

# Note: `/comment/<int:comment_id>/reply` is handled by the above `comment_on_post`
# by passing `parent_comment_id` in the form.
# The frontend will need to ensure the form for a reply includes this hidden field.

# Example of how to register this blueprint in app/__init__.py:
# from .routes import community
# app.register_blueprint(community.bp)
