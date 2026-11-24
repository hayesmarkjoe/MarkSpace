from werkzeug.security import generate_password_hash
import sqlite3
from datetime import datetime

import click
from flask import current_app, g

def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
    app.cli.add_command(create_user_command)

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(
                current_app.config['DATABASE'],
                detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row

    return g.db

def close_db(e=None):
    db = g.pop('db', None)

    if db is not None:
        db.close()

def init_db():
    db = get_db()

    with current_app.open_resource('schema.sql') as f:
        db.executescript(f.read().decode('utf-8'))

@click.command('init-db')
def init_db_command():
    ''' Clear the exisitng data and create new tables.'''
    init_db()
    click.echo('Initialized the database.')

@click.command('create-user')
@click.argument('username')
@click.password_option()
def create_user_command(username, password):
    """Create a user from the command line."""
    db = get_db()
    try:
        db.execute(
            'INSERT INTO user (username, password) VALUES (?, ?)',
            (username, generate_password_hash(password)),
        )
        db.commit()
    except db.IntegrityError:
        click.echo(f'User {username} already exists.')
    else:
        click.echo(f'Created user {username}.')

sqlite3.register_converter(
        "timestamp", lambda v: datetime.fromisoformat(v.decode())
)
