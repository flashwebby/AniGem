class Notification:
    def __init__(self, id, user_id, type, content, link_url=None, is_read=False, created_at=None):
        self.id = id
        self.user_id = user_id  # The recipient of the notification
        self.type = type        # e.g., 'post_reply', 'comment_reply', 'new_follower', etc.
        self.content = content  # Text of the notification, e.g., "User X replied to your post 'Y'."
        self.link_url = link_url # URL to the relevant content, e.g., a post or comment
        self.is_read = is_read
        self.created_at = created_at

    def __repr__(self):
        return f"<Notification {self.id} for User {self.user_id} - Type: {self.type}, Read: {self.is_read}>"
