from flask.ext.security import login_required
from app import app


@app.route('/')
@login_required
def index():
    return 'hello world'
