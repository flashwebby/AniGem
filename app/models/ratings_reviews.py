class Rating:
    def __init__(self, id, user_id, anime_id, score, created_at=None):
        self.id = id
        self.user_id = user_id
        self.anime_id = anime_id
        self.score = score
        self.created_at = created_at

    def __repr__(self):
        return f"<Rating {self.id} - User {self.user_id} Anime {self.anime_id}: {self.score}>"

class Review:
    def __init__(self, id, user_id, anime_id, text_content, rating_id=None, 
                 is_spoiler=False, upvotes=0, downvotes=0, created_at=None, updated_at=None,
                 user=None): # Added user for convenience to hold User object
        self.id = id
        self.user_id = user_id
        self.anime_id = anime_id
        self.rating_id = rating_id
        self.text_content = text_content
        self.is_spoiler = is_spoiler
        self.upvotes = upvotes
        self.downvotes = downvotes
        self.created_at = created_at
        self.updated_at = updated_at
        self.user = user # To store the User object (username, avatar_url)

    def __repr__(self):
        return f"<Review {self.id} - User {self.user_id} Anime {self.anime_id}>"

class ReviewVote:
    def __init__(self, id, user_id, review_id, vote_type, created_at=None):
        self.id = id
        self.user_id = user_id
        self.review_id = review_id
        self.vote_type = vote_type # 'upvote' or 'downvote'
        self.created_at = created_at

    def __repr__(self):
        return f"<ReviewVote {self.id} - User {self.user_id} Review {self.review_id}: {self.vote_type}>"
