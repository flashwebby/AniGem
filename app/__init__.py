import os
from flask import Flask

def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev', # Change this in production!
        DATABASE=os.path.join(app.instance_path, 'flaskr.sqlite'),
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Initialize database functions
    from . import db
    db.init_app(app)

    # Register blueprints
    from .routes import auth
    app.register_blueprint(auth.bp)

    from .routes import user
    app.register_blueprint(user.bp)

    from .routes import anime
    app.register_blueprint(anime.bp)

    from .routes import ratings_reviews
    app.register_blueprint(ratings_reviews.bp)

    from .routes import community 
    app.register_blueprint(community.bp)

    from .routes import user_activity # Added this line
    app.register_blueprint(user_activity.bp) # Added this line

    # Route for the new homepage
    @app.route('/')
    def hello(): # Renaming to 'home' would be more descriptive, but keeping 'hello' as per instruction to modify existing
        from flask import render_template
        return render_template('home.html')

    return app
