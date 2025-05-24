class Subcommunity:
    def __init__(self, id, name, description=None, creator_id=None, created_at=None, creator_username=None): # Added creator_username
        self.id = id
        self.name = name
        self.description = description
        self.creator_id = creator_id
        self.created_at = created_at
        self.creator_username = creator_username # For display purposes

    def __repr__(self):
        return f"<Subcommunity {self.id}: {self.name}>"

class CommunityPost:
    def __init__(self, id, user_id, title, content, subcommunity_id=None, 
                 post_type='discussion', upvotes=0, downvotes=0, 
                 created_at=None, updated_at=None, 
                 user=None, subcommunity=None, comment_count=0): # Added user, subcommunity, comment_count
        self.id = id
        self.user_id = user_id
        self.subcommunity_id = subcommunity_id
        self.title = title
        self.content = content
        self.post_type = post_type # 'discussion', 'meme', 'theory'
        self.upvotes = upvotes
        self.downvotes = downvotes
        self.created_at = created_at
        self.updated_at = updated_at
        self.user = user # User object for author details
        self.subcommunity = subcommunity # Subcommunity object
        self.comment_count = comment_count # To display number of comments

    def __repr__(self):
        return f"<CommunityPost {self.id}: {self.title}>"

class PostVote:
    def __init__(self, id, user_id, post_id, vote_type, created_at=None):
        self.id = id
        self.user_id = user_id
        self.post_id = post_id
        self.vote_type = vote_type # 'upvote' or 'downvote'
        self.created_at = created_at

    def __repr__(self):
        return f"<PostVote {self.id} - User {self.user_id} Post {self.post_id}: {self.vote_type}>"

class Comment:
    def __init__(self, id, user_id, post_id, text_content, parent_comment_id=None, 
                 created_at=None, user=None, replies=None): # Added user and replies
        self.id = id
        self.user_id = user_id
        self.post_id = post_id
        self.parent_comment_id = parent_comment_id
        self.text_content = text_content
        self.created_at = created_at
        self.user = user # User object for commenter details
        self.replies = replies if replies else [] # List of Comment objects (replies)

    def __repr__(self):
        return f"<Comment {self.id} on Post {self.post_id} by User {self.user_id}>"
