class Anime:
    def __init__(self, id, title, description=None, release_year=None, cover_image_url=None, 
                 average_rating=0.0, language=None, created_at=None, updated_at=None,
                 genres=None, tags=None): # Added genres and tags for convenience
        self.id = id
        self.title = title
        self.description = description
        self.release_year = release_year
        self.cover_image_url = cover_image_url
        self.average_rating = average_rating
        self.language = language
        self.created_at = created_at
        self.updated_at = updated_at
        self.genres = genres if genres else [] # List of Genre objects
        self.tags = tags if tags else []       # List of Tag objects

    def __repr__(self):
        return f"<Anime {self.id}: {self.title}>"
