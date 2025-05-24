from flask import Blueprint, render_template, request, redirect, url_for, flash, g, jsonify
from app.db import (
    add_or_update_watchlist_item, remove_watchlist_item, get_watchlist_item_status,
    get_notifications_for_user, mark_notification_as_read, mark_all_notifications_as_read,
    get_anime_by_id, count_unread_notifications # Assuming get_anime_by_id is available
)
from app.routes.auth import login_required

bp = Blueprint('user_activity', __name__)

# Watchlist routes
@bp.route('/anime/<int:anime_id>/watchlist', methods=['POST'])
@login_required
def update_watchlist(anime_id):
    status = request.form.get('status')
    
    if not status:
        return jsonify({'success': False, 'message': 'Status is required.'}), 400

    # Validate status value if necessary (e.g., against a predefined list)
    valid_statuses = ['plan_to_watch', 'completed', 'watching', 'dropped', 'bookmarked', 'remove']
    if status not in valid_statuses:
        return jsonify({'success': False, 'message': 'Invalid status provided.'}), 400

    anime = get_anime_by_id(anime_id)
    if not anime:
        return jsonify({'success': False, 'message': 'Anime not found.'}), 404

    if status == 'remove':
        if remove_watchlist_item(g.user.id, anime_id):
            return jsonify({'success': True, 'message': f"'{anime.title}' removed from your watchlist.", 'new_status': None})
        else:
            return jsonify({'success': False, 'message': 'Failed to remove item from watchlist.'}), 500
    else:
        item_id = add_or_update_watchlist_item(g.user.id, anime_id, status)
        if item_id:
            return jsonify({'success': True, 'message': f"'{anime.title}' status updated to '{status.replace('_', ' ').title()}'." , 'new_status': status})
        else:
            return jsonify({'success': False, 'message': 'Failed to update watchlist.'}), 500

# Notification routes
@bp.route('/notifications')
@login_required
def notifications_page():
    all_notifications = get_notifications_for_user(g.user.id)
    return render_template('user/notifications.html', notifications=all_notifications)

@bp.route('/notifications/<int:notification_id>/read', methods=['POST'])
@login_required
def read_notification(notification_id):
    if mark_notification_as_read(notification_id, g.user.id):
        # If AJAX request, return JSON, else redirect
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': True, 'message': 'Notification marked as read.'})
        flash('Notification marked as read.', 'success')
    else:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': 'Failed to mark as read or notification not found.'}), 400
        flash('Failed to mark notification as read or notification not found.', 'error')
    
    # Redirect to notifications page or origin if specified
    return redirect(request.referrer or url_for('user_activity.notifications_page'))


@bp.route('/notifications/mark_all_read', methods=['POST'])
@login_required
def read_all_notifications():
    if mark_all_notifications_as_read(g.user.id):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': True, 'message': 'All notifications marked as read.'})
        flash('All notifications marked as read.', 'success')
    else:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': 'Failed to mark all notifications as read.'}), 500
        flash('Failed to mark all notifications as read.', 'error')
    return redirect(url_for('user_activity.notifications_page'))

# Context processor to inject unread notification count into all templates
@bp.app_context_processor
def inject_unread_notification_count():
    if g.user:
        return dict(unread_notification_count=count_unread_notifications(g.user.id))
    return dict(unread_notification_count=0)

# Example of how to register this blueprint in app/__init__.py:
# from .routes import user_activity
# app.register_blueprint(user_activity.bp)
