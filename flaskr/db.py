import sqlite3

import click
from flask import current_app, g
from flask.cli import with_appcontext


def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(
            current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        # sqlite3.Row tells the connection to return rows that behave like dicts. This allows accessing the columns by name
        g.db.row_factory = sqlite3.Row

    return g.db


def close_db(e=None):
    db = g.pop('db', None)

    if db is not None:
        db.close()


def init_db():
    db = get_db()
    # open_resource() opens a file relative to the flaskr package
    with current_app.open_resource('schema.sql') as f:
        db.executescript(f.read().decode('utf8'))


# click.command() defines a command line command called init-db that calls the init_db function and shows a success message to the user
@click.command('init-db')
@with_appcontext
def init_db_command():
    """Clear the existing data and create new tables."""
    init_db()
    click.echo('Initialized the database')

@click.command('db-all-users')
@with_appcontext
def db_get_all_users():
    """returns data of all registered users"""
    db = get_db()
    users = db.execute('SELECT * FROM user').fetchall()
    for user in users:
        new_tuple = ()
        for k in user.keys():
            if k != 'password':
                new_tuple = new_tuple + (user[k],)
        print(new_tuple)

# register functions to the application instance
def init_app(app):
    # tells Flask to call that function when cleaning up after returning the response.
    app.teardown_appcontext(close_db)
    # adds a new command that can be called with the flask command.
    app.cli.add_command(init_db_command)
    app.cli.add_command(db_get_all_users)
