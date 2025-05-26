import pytest
from flask import url_for, g
from app.db import get_db, get_post_by_id, get_subcommunity_by_id, get_comments_for_post, get_user_vote_for_post

# Helper to get user ID
def get_user_id_from_username(app, username):
    with app.app_context():
        user = get_db().execute("SELECT id FROM Users WHERE username = ?", (username,)).fetchone()
        return user['id'] if user else None

# Helper to get subcommunity ID
def get_subcommunity_id_by_name(app, name):
    with app.app_context():
        sub = get_db().execute("SELECT id FROM Subcommunities WHERE name = ?", (name,)).fetchone()
        return sub['id'] if sub else None

# Helper to get post ID
def get_post_id_by_title(app, title):
     with app.app_context():
        post = get_db().execute("SELECT id FROM CommunityPosts WHERE title = ?", (title,)).fetchone()
        return post['id'] if post else None

# --- Subcommunity Tests ---
def test_create_subcommunity(client_user1, app, user1_data):
    sub_name = "TestSubCommunity"
    sub_desc = "A place for testing subcommunities."
    
    response_get = client_user1.get(url_for('community.create_subcommunity'))
    assert response_get.status_code == 200 # Page should load

    response_post = client_user1.post(url_for('community.create_subcommunity'), data={
        'name': sub_name,
        'description': sub_desc
    }, follow_redirects=True)
    assert response_post.status_code == 200 # Redirects to sub detail page
    assert f"Subcommunity '{sub_name}' created successfully!".encode() in response_post.data
    
    with app.app_context():
        sub = get_subcommunity_by_id(get_subcommunity_id_by_name(app, sub_name))
        assert sub is not None
        assert sub.name == sub_name
        assert sub.description == sub_desc
        assert sub.creator_id == get_user_id_from_username(app, user1_data['username'])

def test_create_subcommunity_duplicate_name(client_user1, app):
    client_user1.post(url_for('community.create_subcommunity'), data={'name': 'UniqueSub', 'description': ''}) # First one
    response_duplicate = client_user1.post(url_for('community.create_subcommunity'), data={'name': 'UniqueSub', 'description': ''}, follow_redirects=True)
    assert b"already exists" in response_duplicate.data

def test_view_community_home(client, seeded_database): # Use seeded_database if it creates subcommunities/posts
    # Seed some subcommunities and posts if not already done by global fixture
    # For now, assuming `seeded_database` does not create community content.
    # So, this test might initially find an empty community home.
    response = client.get(url_for('community.home'))
    assert response.status_code == 200
    assert b"Welcome to the Community Hub" in response.data
    # Add checks for seeded subcommunities/posts if applicable

def test_view_subcommunity_detail(client, client_user1, app): # User1 creates a sub
    sub_name = "DetailTestSub"
    client_user1.post(url_for('community.create_subcommunity'), data={'name': sub_name, 'description': ''})
    sub_id = get_subcommunity_id_by_name(app, sub_name)
    assert sub_id is not None

    response = client.get(url_for('community.subcommunity_detail', subcommunity_identifier=sub_id))
    assert response.status_code == 200
    assert sub_name.encode() in response.data

    response_by_name = client.get(url_for('community.subcommunity_detail', subcommunity_identifier=sub_name))
    assert response_by_name.status_code == 200
    assert sub_name.encode() in response_by_name.data

# --- Community Post Tests ---
def test_create_post(client_user1, app, user1_data):
    post_title = "My First Test Post"
    post_content = "This is the content of my first test post."
    
    response_get = client_user1.get(url_for('community.create_post'))
    assert response_get.status_code == 200 # Page should load

    response_post = client_user1.post(url_for('community.create_post'), data={
        'title': post_title,
        'content': post_content,
        'post_type': 'discussion' 
        # No subcommunity_id for a general post
    }, follow_redirects=True)
    
    assert response_post.status_code == 200 # Redirects to post detail page
    assert b"Post created successfully!" in response_post.data
    
    with app.app_context():
        post_id = get_post_id_by_title(app, post_title)
        assert post_id is not None
        post = get_post_by_id(post_id)
        assert post.title == post_title
        assert post.content == post_content # Content is fetched by get_post_by_id
        assert post.user_id == get_user_id_from_username(app, user1_data['username'])

def test_create_post_in_subcommunity(client_user1, app, user1_data):
    sub_name = "SubForPosts"
    client_user1.post(url_for('community.create_subcommunity'), data={'name': sub_name, 'description': ''})
    sub_id = get_subcommunity_id_by_name(app, sub_name)

    post_title = "Post in Specific Sub"
    response_post = client_user1.post(url_for('community.create_post', subcommunity_id=sub_id), data={
        'title': post_title,
        'content': "Content for sub post",
    }, follow_redirects=True)
    assert b"Post created successfully!" in response_post.data
    
    with app.app_context():
        post = get_post_by_id(get_post_id_by_title(app, post_title))
        assert post.subcommunity_id == sub_id
        assert post.subcommunity.name == sub_name


def test_view_post_detail(client, client_user1, app):
    post_title = "Viewable Post"
    client_user1.post(url_for('community.create_post'), data={'title': post_title, 'content': "Content"})
    post_id = get_post_id_by_title(app, post_title)

    response = client.get(url_for('community.post_detail', post_id=post_id))
    assert response.status_code == 200
    assert post_title.encode() in response.data
    assert b"Content" in response.data # Check for content
    assert b"Comments" in response.data # Comment section

# --- Comment Tests ---
def test_add_comment_on_post(client_user1, client_user2, app, user1_data, user2_data):
    # User1 creates a post
    post_title = "Post to be Commented On"
    client_user1.post(url_for('community.create_post'), data={'title': post_title, 'content': "Original content"})
    post_id = get_post_id_by_title(app, post_title)
    user1_id = get_user_id_from_username(app, user1_data['username'])
    user2_id = get_user_id_from_username(app, user2_data['username'])

    # User2 comments on User1's post
    comment_text = "This is a comment from User2."
    response_comment = client_user2.post(
        url_for('community.comment_on_post', post_id=post_id),
        data={'text_content': comment_text},
        follow_redirects=True
    )
    assert response_comment.status_code == 200 # Back to post detail
    assert b"Comment posted successfully!" in response_comment.data
    assert comment_text.encode() in response_comment.data # Comment should be visible

    with app.app_context():
        comments = get_comments_for_post(post_id)
        assert len(comments) == 1
        assert comments[0].text_content == comment_text
        assert comments[0].user_id == user2_id
        # Check notification for User1 (post author)
        notifs = get_db().execute(
            "SELECT * FROM Notifications WHERE user_id = ? AND type = 'post_reply'", (user1_id,)
        ).fetchall()
        assert len(notifs) >= 1
        assert post_title in notifs[0]['content']
        assert user2_data['username'] in notifs[0]['content']


def test_reply_to_comment(client_user1, client_user2, app, user1_data, user2_data):
    # User1 posts, User2 comments, User1 replies to User2's comment
    post_title = "Post for Replies"
    client_user1.post(url_for('community.create_post'), data={'title': post_title, 'content': "Content"})
    post_id = get_post_id_by_title(app, post_title)
    user1_id = get_user_id_from_username(app, user1_data['username'])
    user2_id = get_user_id_from_username(app, user2_data['username'])

    # User2's first comment
    first_comment_text = "User2 first comment."
    client_user2.post(url_for('community.comment_on_post', post_id=post_id), data={'text_content': first_comment_text})
    
    parent_comment_id = None
    with app.app_context():
        comments_after_first = get_comments_for_post(post_id)
        parent_comment_id = comments_after_first[0].id

    assert parent_comment_id is not None

    # User1 replies to User2's comment
    reply_text = "User1 replying to User2."
    response_reply = client_user1.post(
        url_for('community.comment_on_post', post_id=post_id),
        data={'text_content': reply_text, 'parent_comment_id': parent_comment_id},
        follow_redirects=True
    )
    assert b"Comment posted successfully!" in response_reply.data
    assert reply_text.encode() in response_reply.data

    with app.app_context():
        comments = get_comments_for_post(post_id)
        assert len(comments) == 1 # Still one top-level comment
        assert len(comments[0].replies) == 1
        assert comments[0].replies[0].text_content == reply_text
        assert comments[0].replies[0].user_id == user1_id
        # Check notification for User2 (parent comment author)
        notifs = get_db().execute(
            "SELECT * FROM Notifications WHERE user_id = ? AND type = 'comment_reply'", (user2_id,)
        ).fetchall()
        assert len(notifs) >= 1
        assert post_title in notifs[0]['content']
        assert user1_data['username'] in notifs[0]['content']


# --- Post Vote Tests ---
def test_vote_post(client_user1, client_user2, app, user1_data, user2_data):
    post_title = "Post to be Voted On"
    client_user1.post(url_for('community.create_post'), data={'title': post_title, 'content': "Vote content"})
    post_id = get_post_id_by_title(app, post_title)
    user2_id = get_user_id_from_username(app, user2_data['username'])

    # User2 upvotes User1's post
    response_upvote = client_user2.post(url_for('community.vote_post', post_id=post_id), data={'vote_type': 'upvote'})
    assert response_upvote.status_code == 200 # AJAX route returns JSON
    json_data_up = response_upvote.get_json()
    assert json_data_up['success'] is True
    assert json_data_up['upvotes'] == 1
    assert json_data_up['downvotes'] == 0
    assert json_data_up['new_vote_status'] == 'upvote'

    with app.app_context():
        post = get_post_by_id(post_id)
        assert post.upvotes == 1
        assert get_user_vote_for_post(user2_id, post_id) == 'upvote'

    # User2 changes vote to downvote
    response_downvote = client_user2.post(url_for('community.vote_post', post_id=post_id), data={'vote_type': 'downvote'})
    json_data_down = response_downvote.get_json()
    assert json_data_down['success'] is True
    assert json_data_down['upvotes'] == 0
    assert json_data_down['downvotes'] == 1
    assert json_data_down['new_vote_status'] == 'downvote'
    
    # User2 removes their downvote (clicks downvote again)
    response_none = client_user2.post(url_for('community.vote_post', post_id=post_id), data={'vote_type': 'downvote'})
    json_data_none = response_none.get_json()
    assert json_data_none['success'] is True
    assert json_data_none['upvotes'] == 0
    assert json_data_none['downvotes'] == 0
    assert json_data_none['new_vote_status'] is None
```
