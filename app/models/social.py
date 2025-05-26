class Friendship:
    def __init__(self, user_id_1, user_id_2, status, requested_at=None, accepted_at=None, 
                 # Helper attributes for displaying friend information
                 friend_id=None, friend_username=None, friend_avatar_url=None):
        # Ensure user_id_1 < user_id_2 for consistency in storage, if required by DB schema
        # However, for the object itself, it might be fine to store as is and handle order in DB layer.
        # For this model, let's assume they are passed in the correct order or DB handles it.
        self.user_id_1 = user_id_1
        self.user_id_2 = user_id_2
        self.status = status  # 'pending', 'accepted', 'blocked'
        self.requested_at = requested_at
        self.accepted_at = accepted_at
        
        # These are not part of the Friendships table directly but are useful for display
        self.friend_id = friend_id 
        self.friend_username = friend_username
        self.friend_avatar_url = friend_avatar_url


    def __repr__(self):
        return f"<Friendship ({self.user_id_1}, {self.user_id_2}) - Status: {self.status}>"

class DirectMessage:
    def __init__(self, id, sender_id, receiver_id, message_content, sent_at=None, is_read=False, 
                 sender_username=None, receiver_username=None): # Usernames for convenience
        self.id = id
        self.sender_id = sender_id
        self.receiver_id = receiver_id
        self.message_content = message_content
        self.sent_at = sent_at
        self.is_read = is_read
        self.sender_username = sender_username # Not in DB table, for display
        self.receiver_username = receiver_username # Not in DB table, for display


    def __repr__(self):
        return f"<DirectMessage {self.id} from {self.sender_id} to {self.receiver_id} at {self.sent_at}>"

class ConversationPreview:
    """
    A helper class, not directly mapped to a table.
    Used to display a list of conversations on the messages_home.html page.
    """
    def __init__(self, other_user_id, other_user_username, other_user_avatar_url,
                 last_message_content, last_message_sent_at, unread_count=0):
        self.other_user_id = other_user_id
        self.other_user_username = other_user_username
        self.other_user_avatar_url = other_user_avatar_url
        self.last_message_content = last_message_content
        self.last_message_sent_at = last_message_sent_at
        self.unread_count = unread_count

    def __repr__(self):
        return f"<ConversationPreview with {self.other_user_username}, Unread: {self.unread_count}>"
