import pytest
from flask import url_for, g
from app.db import (
    get_db, get_friendship_status, get_friends, get_pending_friend_requests,
    get_direct_messages, get_conversations, count_unread_direct_messages,
    find_user_by_id # For various checks
)

# Helper to get user ID
def get_user_id(app, username):
    with app.app_context():
        user = get_db().execute("SELECT id FROM Users WHERE username = ?", (username,)).fetchone()
        return user['id'] if user else None

# --- User Search Tests ---
def test_user_search(client_user1, app, user1_data, registered_user2): # user2 is also registered
    user2_username = user2_data['username']
    
    # Search for an existing user
    response = client_user1.post(url_for('social.user_search'), data={'username_query': user2_username}, follow_redirects=True)
    assert response.status_code == 200
    assert f"Search Results for \"{user2_username}\"".encode() in response.data
    assert user2_username.encode() in response.data
    assert b"Add Friend" in response.data # Assuming not friends yet

    # Search for a non-existent user
    response_non_existent = client_user1.post(url_for('social.user_search'), data={'username_query': 'no_such_user_xyz'}, follow_redirects=True)
    assert response_non_existent.status_code == 200
    assert b"No users found" in response_non_existent.data

    # Search for self (should not show "Add Friend" or other actions)
    response_self = client_user1.post(url_for('social.user_search'), data={'username_query': user1_data['username']}, follow_redirects=True)
    assert response_self.status_code == 200
    assert user1_data['username'].encode() in response_self.data
    assert b"Add Friend" not in response_self.data # Cannot add self

# --- Friendship Management Tests ---
def test_send_friend_request(client_user1, client_user2, app, user1_data, user2_data):
    user1_id = get_user_id(app, user1_data['username'])
    user2_id = get_user_id(app, user2_data['username'])

    # User1 sends request to User2
    response = client_user1.post(url_for('social.send_request_route', target_user_id=user2_id), follow_redirects=True)
    assert response.status_code == 200 # Redirects to target user's profile or referrer
    assert f"Friend request sent to {user2_data['username']}".encode() in response.data
    
    with app.app_context():
        status = get_friendship_status(user1_id, user2_id)
        assert status == 'pending'
        # Check notification for User2
        notifs = get_db().execute(
            "SELECT * FROM Notifications WHERE user_id = ? AND type = 'friend_request'", (user2_id,)
        ).fetchall()
        assert len(notifs) >= 1
        assert user1_data['username'] in notifs[0]['content']

    # Try sending again (should indicate pending)
    response_again = client_user1.post(url_for('social.send_request_route', target_user_id=user2_id), follow_redirects=True)
    assert b"Friend request is already pending." in response_again.data


def test_accept_friend_request(client_user1, client_user2, app, user1_data, user2_data):
    user1_id = get_user_id(app, user1_data['username'])
    user2_id = get_user_id(app, user2_data['username'])
    
    # User1 sends request to User2
    client_user1.post(url_for('social.send_request_route', target_user_id=user2_id))

    # User2 accepts User1's request
    response = client_user2.post(url_for('social.accept_request_route', target_user_id=user1_id), follow_redirects=True)
    assert response.status_code == 200 # Redirects to friend requests page or referrer
    assert f"Friend request from {user1_data['username']} accepted.".encode() in response.data

    with app.app_context():
        status = get_friendship_status(user1_id, user2_id)
        assert status == 'accepted'
        friends_of_user1 = get_friends(user1_id)
        assert any(f.friend_id == user2_id for f in friends_of_user1)


def test_reject_friend_request(client_user1, client_user2, app, user1_data, user2_data):
    user1_id = get_user_id(app, user1_data['username'])
    user2_id = get_user_id(app, user2_data['username'])
    client_user1.post(url_for('social.send_request_route', target_user_id=user2_id))

    # User2 rejects User1's request
    response = client_user2.post(url_for('social.reject_request_route', target_user_id=user1_id), follow_redirects=True)
    assert f"Friend request from {user1_data['username']} rejected.".encode() in response.data
    
    with app.app_context():
        assert get_friendship_status(user1_id, user2_id) is None # Row is deleted


def test_remove_friend(client_user1, client_user2, app, user1_data, user2_data):
    user1_id = get_user_id(app, user1_data['username'])
    user2_id = get_user_id(app, user2_data['username'])
    client_user1.post(url_for('social.send_request_route', target_user_id=user2_id))
    client_user2.post(url_for('social.accept_request_route', target_user_id=user1_id)) # They are friends

    # User1 removes User2
    response = client_user1.post(url_for('social.remove_friend_route', target_user_id=user2_id), follow_redirects=True)
    assert f"{user2_data['username']} has been removed from your friends list.".encode() in response.data
    with app.app_context():
        assert get_friendship_status(user1_id, user2_id) is None


def test_block_unblock_user(client_user1, client_user2, app, user1_data, user2_data):
    user1_id = get_user_id(app, user1_data['username'])
    user2_id = get_user_id(app, user2_data['username'])

    # User1 blocks User2
    response_block = client_user1.post(url_for('social.block_user_route', target_user_id=user2_id), follow_redirects=True)
    assert f"{user2_data['username']} has been blocked.".encode() in response_block.data
    with app.app_context():
        assert get_friendship_status(user1_id, user2_id) == 'blocked'
    
    # User1 tries to send friend request to blocked User2 (should fail or be handled)
    # The current `send_friend_request` checks `get_friendship_status`
    response_send_req_blocked = client_user1.post(url_for('social.send_request_route', target_user_id=user2_id), follow_redirects=True)
    assert b"Relationship is blocked" in response_send_req_blocked.data


    # User1 unblocks User2
    response_unblock = client_user1.post(url_for('social.unblock_user_route', target_user_id=user2_id), follow_redirects=True)
    assert f"{user2_data['username']} has been unblocked.".encode() in response_unblock.data
    with app.app_context():
        assert get_friendship_status(user1_id, user2_id) is None # Blocked status removed

# --- Direct Messaging Tests ---
def test_send_direct_message(client_user1, client_user2, app, user1_data, user2_data):
    user1_id = get_user_id(app, user1_data['username'])
    user2_id = get_user_id(app, user2_data['username'])
    
    # For DMs, users don't strictly need to be friends by current schema, but typically are.
    # Let's make them friends for a more realistic scenario.
    client_user1.post(url_for('social.send_request_route', target_user_id=user2_id))
    client_user2.post(url_for('social.accept_request_route', target_user_id=user1_id))

    message_text = "Hello from User1!"
    response = client_user1.post(
        url_for('social.send_dm_route', receiver_id=user2_id),
        data={'message_content': message_text},
        follow_redirects=True
    )
    assert response.status_code == 200 # Redirects to conversation page
    assert b"Message sent!" in response.data
    assert message_text.encode() in response.data # Message should be on the page

    with app.app_context():
        messages = get_direct_messages(user1_id, user2_id)
        assert len(messages) == 1
        assert messages[0].message_content == message_text
        assert messages[0].sender_id == user1_id
        assert messages[0].receiver_id == user2_id
        assert messages[0].is_read is False # Initially unread by receiver

def test_view_conversation_and_mark_read(client_user1, client_user2, app, user1_data, user2_data):
    user1_id = get_user_id(app, user1_data['username'])
    user2_id = get_user_id(app, user2_data['username'])
    client_user1.post(url_for('social.send_dm_route', receiver_id=user2_id), data={'message_content': "Msg1 from U1"})
    client_user2.post(url_for('social.send_dm_route', receiver_id=user1_id), data={'message_content': "Msg2 from U2"})
    client_user1.post(url_for('social.send_dm_route', receiver_id=user2_id), data={'message_content': "Msg3 from U1"})

    # User2 views conversation with User1
    # This should mark messages from User1 to User2 as read.
    response_user2_view = client_user2.get(url_for('social.conversation_detail', other_user_id=user1_id))
    assert response_user2_view.status_code == 200
    assert b"Msg1 from U1" in response_user2_view.data
    assert b"Msg3 from U1" in response_user2_view.data
    
    with app.app_context():
        # Messages sent by user1 to user2 should now be read
        msgs_from_u1 = get_db().execute(
            "SELECT * FROM DirectMessages WHERE sender_id = ? AND receiver_id = ? ORDER BY sent_at",
            (user1_id, user2_id)
        ).fetchall()
        assert all(m['is_read'] == 1 for m in msgs_from_u1) # 1 for True

        # Messages sent by user2 to user1 should still be unread by user1
        msgs_from_u2 = get_db().execute(
            "SELECT * FROM DirectMessages WHERE sender_id = ? AND receiver_id = ? ORDER BY sent_at",
            (user2_id, user1_id)
        ).fetchall()
        assert all(m['is_read'] == 0 for m in msgs_from_u2) # 0 for False

def test_messages_home_unread_counts(client_user1, client_user2, app, user1_data, user2_data):
    user1_id = get_user_id(app, user1_data['username'])
    user2_id = get_user_id(app, user2_data['username'])

    # User2 sends a message to User1
    client_user2.post(url_for('social.send_dm_route', receiver_id=user1_id), data={'message_content': "DM for count test"})
    
    # User1 views messages home page
    response_user1_home = client_user1.get(url_for('social.messages_home'))
    assert response_user1_home.status_code == 200
    # Check for User2's conversation with an unread badge
    # The ConversationPreview object has unread_count. Template should show it.
    assert user2_data['username'].encode() in response_user1_home.data
    assert b'<span class="unread-badge">1</span>' in response_user1_home.data # Assuming 1 unread from user2

    # Also check global unread DM count in nav (if base.html is rendered with this context)
    # This relies on the app_context_processor for unread_dm_count
    response_any_page = client_user1.get(url_for('hello')) # Any page that renders base.html
    assert b'Messages <span class="badge" id="unread-dm-count">1</span>' in response_any_page.data


# --- Friends Activity Feed Test (Basic) ---
def test_friends_activity_feed(client_user1, seeded_database): # seeded_database for anime
    # This test is basic as get_friends_activity is a placeholder.
    # It should load the page. If get_friends_activity is implemented, add data checks.
    response = client_user1.get(url_for('social.friends_activity_feed'))
    assert response.status_code == 200
    assert b"What Your Friends Are Watching" in response.data
    # Check for "No recent activity" if the function returns empty
    assert b"No recent activity from your friends" in response.data \
        or b"No activities to display" in response.data # Adjust based on template text


# Test Profile Page Friendship Actions Display (already partially covered by profile tests, but focus here)
def test_profile_page_friendship_actions(client_user1, client_user2, app, user1_data, user2_data):
    user2_id = get_user_id(app, user2_data['username'])
    
    # Scenario 1: User1 views User2's profile (not friends)
    response_view_stranger = client_user1.get(url_for('user.profile', username=user2_data['username']))
    assert response_view_stranger.status_code == 200
    assert b"Add Friend" in response_view_stranger.data # Action available

    # Scenario 2: User1 sends request to User2, then views User2's profile
    client_user1.post(url_for('social.send_request_route', target_user_id=user2_id))
    response_view_pending = client_user1.get(url_for('user.profile', username=user2_data['username']))
    assert b"Request Pending" in response_view_pending.data # Or "Cancel Request"

    # Scenario 3: User2 accepts, User1 views User2's profile (now friends)
    client_user2.post(url_for('social.accept_request_route', target_user_id=get_user_id(app, user1_data['username'])))
    response_view_friend = client_user1.get(url_for('user.profile', username=user2_data['username']))
    assert b"Remove Friend" in response_view_friend.data
    assert b"Send Message" in response_view_friend.data

    # Scenario 4: User1 blocks User2, then views User2's profile
    client_user1.post(url_for('social.block_user_route', target_user_id=user2_id))
    response_view_blocked = client_user1.get(url_for('user.profile', username=user2_data['username']))
    # The text might be "Interaction Blocked" or specific "Unblock" button
    assert b"Interaction Blocked" in response_view_blocked.data or b"Unblock" in response_view_blocked.data
```
