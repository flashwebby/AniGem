import pytest
from flask import url_for, g
from app.db import (
    get_db, get_watchlist_for_user, get_watchlist_item_status,
    get_notifications_for_user, count_unread_notifications,
    create_notification # For direct testing if needed
)

# Helper to get an anime ID
def get_anime_id_by_title(app, title="Code Geass: Lelouch of the Rebellion"):
    with app.app_context():
        anime = get_db().execute("SELECT id FROM Anime WHERE title = ?", (title,)).fetchone()
        assert anime is not None, f"Anime '{title}' not found in seeded data for test setup."
        return anime['id']

# Helper to get user ID
def get_user_id(app, username):
    with app.app_context():
        user = get_db().execute("SELECT id FROM Users WHERE username = ?", (username,)).fetchone()
        return user['id'] if user else None

# --- Watchlist Tests ---
def test_add_to_watchlist(client_user1, app, seeded_database, user1_data):
    anime_id = get_anime_id_by_title(app)
    user_id = get_user_id(app, user1_data['username'])

    # Add to "plan_to_watch"
    response = client_user1.post(
        url_for('user_activity.update_watchlist', anime_id=anime_id),
        data={'status': 'plan_to_watch'}
    )
    assert response.status_code == 200 # AJAX route returns JSON
    json_data = response.get_json()
    assert json_data['success'] is True
    assert json_data['new_status'] == 'plan_to_watch'
    
    with app.app_context():
        status = get_watchlist_item_status(user_id, anime_id)
        assert status == 'plan_to_watch'

    # Update status to "watching"
    client_user1.post(url_for('user_activity.update_watchlist', anime_id=anime_id), data={'status': 'watching'})
    with app.app_context():
        assert get_watchlist_item_status(user_id, anime_id) == 'watching'

    # Remove from watchlist
    response_remove = client_user1.post(
        url_for('user_activity.update_watchlist', anime_id=anime_id),
        data={'status': 'remove'} # Using the special 'remove' status
    )
    assert response_remove.status_code == 200
    json_data_remove = response_remove.get_json()
    assert json_data_remove['success'] is True
    assert json_data_remove['new_status'] is None # Item removed

    with app.app_context():
        assert get_watchlist_item_status(user_id, anime_id) is None


def test_view_watchlist_on_profile(client_user1, app, seeded_database, user1_data):
    anime1_id = get_anime_id_by_title(app, "Code Geass: Lelouch of the Rebellion")
    anime2_id = get_anime_id_by_title(app, "K-On!")
    
    # Add items to watchlist
    client_user1.post(url_for('user_activity.update_watchlist', anime_id=anime1_id), data={'status': 'completed'})
    client_user1.post(url_for('user_activity.update_watchlist', anime_id=anime2_id), data={'status': 'plan_to_watch'})

    response = client_user1.get(url_for('user.profile', username=user1_data['username']))
    assert response.status_code == 200
    assert b"My Watchlists" in response.data
    assert b"Code Geass" in response.data # Should be under "Completed"
    assert b"K-On!" in response.data      # Should be under "Plan to Watch"
    # Check tab structure if specific enough
    assert b"Completed (1)" in response.data 
    assert b"Plan to Watch (1)" in response.data


# --- Notification Tests ---
# Notification creation is tested indirectly via test_community.py (comment notifications)
# and will be tested in test_social.py (friend request notifications).
# Here we test fetching and marking notifications as read.

def test_view_notifications_page(client_user1, app, user1_data):
    user_id = get_user_id(app, user1_data['username'])
    # Manually create a notification for this user for testing
    with app.app_context():
        create_notification(user_id, 'test_notification', 'This is a test notification.', url_for('hello'))

    response = client_user1.get(url_for('user_activity.notifications_page'))
    assert response.status_code == 200
    assert b"Notifications" in response.data
    assert b"This is a test notification." in response.data

    # Check unread count (should be at least 1)
    # The inject_unread_notification_count context processor makes this available.
    # We can check it on any page, e.g., the notifications page itself or home.
    assert b'Notifications <span class="badge" id="unread-notifications-count">1</span>' in response.data \
        or b'Notifications <span class="badge" id="unread-notifications-count">2</span>' in response.data # Depending on other tests

def test_mark_notification_as_read(client_user1, app, user1_data):
    user_id = get_user_id(app, user1_data['username'])
    notification_id = None
    with app.app_context():
        notification_id = create_notification(user_id, 'test_read_single', 'Test single read.')
        assert notification_id is not None
        assert count_unread_notifications(user_id) >= 1

    response = client_user1.post(url_for('user_activity.read_notification', notification_id=notification_id), follow_redirects=True)
    assert response.status_code == 200
    assert b"Notification marked as read." in response.data
    
    with app.app_context():
        notif = get_db().execute("SELECT is_read FROM Notifications WHERE id = ?", (notification_id,)).fetchone()
        assert notif['is_read'] == 1 # 1 for True in SQLite

def test_mark_all_notifications_as_read(client_user1, app, user1_data):
    user_id = get_user_id(app, user1_data['username'])
    with app.app_context():
        create_notification(user_id, 'test_read_all_1', 'Notification 1 for all read.')
        create_notification(user_id, 'test_read_all_2', 'Notification 2 for all read.')
        assert count_unread_notifications(user_id) >= 2

    response = client_user1.post(url_for('user_activity.read_all_notifications'), follow_redirects=True)
    assert response.status_code == 200
    assert b"All notifications marked as read." in response.data
    
    with app.app_context():
        assert count_unread_notifications(user_id) == 0

def test_unread_notification_count_display(client_user1, app, user1_data):
    user_id = get_user_id(app, user1_data['username'])
    
    # Ensure initially 0 or some known state from other tests if run in sequence without perfect isolation
    # For robustness, let's clear and set.
    with app.app_context():
        get_db().execute("DELETE FROM Notifications WHERE user_id = ?", (user_id,))
        get_db().commit()
        assert count_unread_notifications(user_id) == 0

    # Check count is initially empty or 0 on a page
    response_initial = client_user1.get(url_for('hello')) # Any page
    assert b'Notifications <span class="badge" id="unread-notifications-count"></span>' in response_initial.data \
        or b'Notifications <span class="badge" id="unread-notifications-count">0</span>' in response_initial.data \
        or b'id="unread-notifications-count">\n            </span>' in response_initial.data # handles whitespace variation

    # Create a notification
    with app.app_context():
        create_notification(user_id, 'test_count_display', 'Testing count display.')
    
    response_after = client_user1.get(url_for('hello'))
    assert b'Notifications <span class="badge" id="unread-notifications-count">1</span>' in response_after.data

# Test notification creation on comment (already partially done in test_community.py)
# This is more of an integration test point.
def test_notification_on_post_reply(client_user1, client_user2, app, user1_data, user2_data, seeded_database):
    user1_id = get_user_id(app, user1_data['username'])
    # User1 creates a post
    post_title = "Post for Notification Test"
    client_user1.post(url_for('community.create_post'), data={'title': post_title, 'content': "Content"})
    post_id = get_post_id_by_title(app, post_title) # Helper from test_community

    # User2 comments on User1's post
    client_user2.post(url_for('community.comment_on_post', post_id=post_id), data={'text_content': "A new comment"})
    
    with app.app_context():
        notifications_for_user1 = get_notifications_for_user(user1_id, only_unread=True)
        assert len(notifications_for_user1) >= 1
        reply_notification = next((n for n in notifications_for_user1 if n.type == 'post_reply'), None)
        assert reply_notification is not None
        assert post_title in reply_notification.content
        assert user2_data['username'] in reply_notification.content
```
