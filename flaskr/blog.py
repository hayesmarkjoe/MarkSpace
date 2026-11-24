from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from flaskr.auth import login_required
from flaskr.db import get_db

bp = Blueprint('blog', __name__)

SECTIONS = ('blog', 'projects')

@bp.app_template_filter('preview')
def preview(text, lines=4):
    split = text.splitlines()
    return '\n'.join(split[:lines]) + ('\n_' if len(split) > lines else '')

@bp.route('/')
def index():
    # Home page = About
    return render_template('blog/about.html')

@bp.route('/<any("blog", "projects"):section>')
def section_list(section):
    db = get_db()
    posts = db.execute(
        'SELECT p.id, title, body, created, author_id, username, section'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' WHERE p.section = ?'
        ' ORDER BY created DESC',
        (section,)
    ).fetchall()

    replies = db.execute(
        'SELECT r.id, r.post_id, r.body, r.created, r.author_id, u.username'
        ' FROM reply r JOIN user u ON r.author_id = u.id'
        ' ORDER BY r.created ASC',
    ).fetchall()

    replies_by_post = {}
    for r in replies:
        replies_by_post.setdefault(r['post_id'], []).append(r)

    return render_template('blog/index.html',
                           posts=posts,
                           replies_by_post=replies_by_post,
                           section=section)

@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        section = request.form['section']
        error = None

        if not title:
            error = 'Title is required.'
        elif section not in SECTIONS:
            error = 'Invalid section.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'INSERT INTO post (title, body, section, author_id)'
                ' VALUES (?, ?, ?, ?)',
                (title, body, section, g.user['id'])
            )
            db.commit()
            return redirect(url_for('blog.section_list', section=section))
    return render_template('blog/create.html')

@bp.route('/<int:id>/reply', methods=('GET', 'POST'))
@login_required
def reply(id):
    post = get_post(id, check_author=False)

    if request.method == 'POST':
        body = request.form['body']
        error = None

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                    'INSERT INTO reply (post_id, author_id, body)'
                    ' VALUES (?, ?, ?)',
                    (id, g.user['id'], body)
            )
            db.commit()
            return redirect(url_for('blog.section_list',
                                    section=post['section']))
    return render_template('blog/reply.html', post=post)    

# function to get post by id for both update and delete
def get_post(id, check_author=True):
    post = get_db().execute(
        'SELECT p.id, title, body, created, author_id, username, section'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' WHERE p.id = ?',
        (id,)
    ).fetchone()
       
    if post is None:
        abort(404, f"Post id {id} doesn't exist.")

    if check_author and post['author_id'] != g.user['id']:
        abort(403)

    return post


@bp.route('/post/<int:id>')
def detail(id):
    post = get_post(id, check_author=False)

    replies = get_db().execute(
            'SELECT r.id, r.post_id, r.body, r.created, r.author_id, u.username'
        ' FROM reply r JOIN user u ON r.author_id = u.id'
        ' WHERE r.post_id = ?'
        ' ORDER BY r.created ASC',
        (id,)
    ).fetchall()

    return render_template('blog/detail.html', post=post, replies=replies)
@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    post = get_post(id)

    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        section = request.form['section']
        error = None

        if not title:
            error = 'Title is required.'
        elif section not in SECTIONS:
            error = 'Invalid section'
       
        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'UPDATE post SET title = ?, body = ?, section = ?'
                ' WHERE id = ?',
                (title, body, section, id)
            )
            db.commit()
            return redirect(url_for('blog..section_list', section=section))

    return render_template('blog/update.html', post=post)


@bp.route('/<int:id>/delete', methods=('POST', ))
@login_required
def delete(id):
    get_post(id)
    db = get_db()
    db.execute('DELETE FROM post WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('blog.index'))
