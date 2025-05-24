class Genre:
    def __init__(self, id, name):
        self.id = id
        self.name = name

    def __repr__(self):
        return f"<Genre {self.id}: {self.name}>"

class Tag:
    def __init__(self, id, name):
        self.id = id
        self.name = name

    def __repr__(self_):
        return f"<Tag {self.id}: {self.name}>"
