import os
from flask import Flask
import markdown, bleach
from markupsafe import Markup

def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
            SECRET_KEY='dev',
            DATABASE=os.path.join(app.instance_path, 'flaskr.sqlite'),
    )
    if test_config is None:
        #load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config, if passed in
        app.config.from_mapping(test_config)

    #ensure the instance folder exists
    os.makedirs(app.instance_path, exist_ok=True)
    
    @app.route('/hello')
    def hello():
        return '<h1>Hello MFS</h1>' 

    from . import db
    db.init_app(app)

    from . import auth
    app.register_blueprint(auth.bp)
    
    from . import blog
    app.register_blueprint(blog.bp)
    app.add_url_rule('/', endpoint='index')

    ALLOWED_TAGS = list(bleach.sanitizer.ALLOWED_TAGS) + [
            "p", "pre", "code", "span", "div", "h1", "h2", "h3", 
            "h4", "ul", "ol", "li", "br", "hr", 
    ]
    ALLOWED_ATTRS = {"*": ["class"], "a": ["href", "title"]}

    def render_markdown(text):
        html = markdown.markdown(
                text or "",
                extensions=["fenced_code", "codehilite", "nl2br"],
                extension_configs={"codehilite": {"guess_lang": False}}
        )
        return Markup(bleach.clean(html, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRS))

    app.add_template_filter(render_markdown, "md")

    return app

