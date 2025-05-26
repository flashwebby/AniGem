class WatchlistItem:
    def __init__(self, id, user_id, anime_id, status, added_at=None, anime=None): # anime object for convenience
        self.id = id
        self.user_id = user_id
        self.anime_id = anime_id
        self.status = status  # e.g., 'plan_to_watch', 'completed', 'watching', 'dropped', 'bookmarked'
        self.added_at = added_at
        self.anime = anime # To hold Anime object (title, cover_image_url) for display

    def __repr__(self):
        return f"<WatchlistItem {self.id} - User {self.user_id}, Anime {self.anime_id}: {self.status}>"
