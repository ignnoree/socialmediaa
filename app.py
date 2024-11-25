from flask import Flask, request, redirect, render_template, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from cs50 import SQL
from profilequery import profile_query, home_query
from functionts import ifpost_contents, getusername
from flask_socketio import SocketIO, emit, join_room


db = SQL('sqlite:///mydatabase.db')
app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['DEBUG'] = True
db.execute('PRAGMA foreign_keys = ON')
socketio = SocketIO(app)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' not in session:
        if request.method == 'POST':
            username = request.form.get("username")
            password = request.form.get("password")
            email = request.form.get("email")
            if not (username and password and email):
                return render_template('register.html', massage='ALL FIELDS ARE REQUIRED!')

            hashed_password = generate_password_hash(password)
            db.execute('INSERT INTO users(username,email,password) VALUES (?,?,?)',
                    username, email, hashed_password)
            return redirect('/login')
        return render_template('register.html')
    else:
        return redirect('/')


@app.route('/login', methods=['POST', 'GET'])
def login():
    if 'user_id' not in session:
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            user = db.execute('select * from users where username =?', username)
            user = user[0]if user else None
            if user and check_password_hash(user['password'], password):
                session['user_id'] = user['id']
                flash('login succsessfull!')
                return redirect('/')
            else:
                return render_template('login.html', message='invalid login credentials')
        return render_template('login.html')
    else:
        return redirect('/')


@app.route('/logout')
def logout():
    if 'user_id' in session:
        session.clear()
        return redirect('register')


@app.route('/', methods=['POST', 'GET', 'PUT'])
def home():
    user = session.get('user_id')
    if not user:
        return redirect('/register')
    username = getusername(user)

    if request.method == 'POST':

        action = request.form.get('action')

        if username:
            ifpost_contents(username, action)
            return redirect('/')

    result = db.execute(home_query,user)
    posts_with_comments = {}
    liked_data = db.execute(
        'SELECT post_id, COUNT(*) AS like_count FROM likes GROUP BY post_id')

    likes_count = {}
    for i in liked_data:
        likes_count[i['post_id']] = i['like_count']
    for i in result:
        post_id = i['post_id']
        if post_id not in posts_with_comments:
            posts_with_comments[post_id] = {
                'id': post_id,
                'username': i['posts_author'],
                'content': i['posts_content'],
                'created_at': i['post_created_at'],
                'comments': [],
                'liked_count': likes_count.get(post_id, 0)

            }
        if i['comment_id']:
            posts_with_comments[post_id]['comments'].append({
                'comment_id': i['comment_id'],
                'comment_author': i['comment_author'],
                'comment_content': i['comment']
            })
    

    return render_template('home.html', posts=posts_with_comments, username=username)


@app.route('/profile/<username>', methods=['POST', 'GET'])
def profile(username):
    profile_user = db.execute('SELECT * FROM users WHERE username = ?', username)
    profile_user = profile_user[0] if profile_user else None
    user_id=session.get('user_id')
    followed_id=profile_user['id']
    if request.method == 'POST':
        action = request.form.get('action')
        

        if action=='FOLLOW':
            existing_follows=db.execute('select * from followers where follower_id = ? and followed_id=?',user_id,followed_id)
            if existing_follows:
                db.execute('delete from followers where follower_id = ? and followed_id = ? ',user_id,followed_id)
            else:
                db.execute('insert into followers (follower_id,followed_id) VALUES (?,?) ',user_id,followed_id)

        ifpost_contents(username, action)
        return redirect(f'{username}')
        

    elif request.method == 'GET':
        followers=db.execute('select count(*)from followers where follower_id = ?',followed_id)
        followers_count=followers[0]['count(*)']if followers else 0
        print(f'11111{followers_count}')
        followings=db.execute('select count(*)from followers where followed_id = ?',followed_id)
        followings_count=followings[0]['count(*)'] if followings else 0
        followed_id = profile_user['id']
        is_following = bool(db.execute('SELECT * FROM followers WHERE follower_id = ? AND followed_id = ?', user_id, followed_id))
        result = db.execute(profile_query, username)
        posts_with_comments = {}
        liked_data = db.execute(
            'SELECT post_id, COUNT(*) AS like_count FROM likes GROUP BY post_id')

        likes_count = {}
        for i in liked_data:
            likes_count[i['post_id']] = i['like_count']
        for i in result:
            post_id = i['post_id']
            if post_id not in posts_with_comments:
                posts_with_comments[post_id] = {
                    'id': post_id,
                    'username': i['post_author'],
                    'content': i['post_content'],
                    'created_at': i['post_created_at'],
                    'comments': [],
                    'liked_count': likes_count.get(post_id, 0)

                }
            if i['comment_id']:
                posts_with_comments[post_id]['comments'].append({
                    'comment_id': i['comment_id'],
                    'comment_author': i['comment_author'],
                    'comment_content': i['comment_content']
                })

        return render_template('profile.html', posts_with_comments=posts_with_comments, username=username,profile_user=profile_user,is_following=is_following,followers_count=followers_count,followings_count=followings_count)


@app.route('/delete',methods = ['GET' , 'POST'])
def deleteaccount():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'delete-account':
            username = getusername(session.get('user_id'))
            db.execute('delete from posts where username=?',username)
            db.execute('delete from likes where author = ?',username)
            db.execute('delete from comments where username= ?', username)
            db.execute('delete from users where username= ?', username)

            return redirect('')
    elif request.method == 'GET':
        return render_template('deleteacc.html',)


@app.route('/explore')
def explore():
    if request.method=='POST':
        pass
    
    profiles=db.execute('select username from users')

    return render_template('explore.html',profiles=profiles)



@app.route('/direct/<receiver_username>', methods=['GET'])
def direct(receiver_username):
    if 'user_id' not in session:
        return redirect('/login')
    
    sender_id = session['user_id']
    receiver = db.execute('SELECT id, username FROM users WHERE username = ?', receiver_username)
    receiver = receiver[0] if receiver else None

    if not receiver:
        return "User not found", 404

    receiver_id = receiver['id']
    messages = db.execute('''
        SELECT 
    messages.content, 
    messages.timestamp, 
    (SELECT username FROM users WHERE users.id = messages.sender_id) AS sender_username, -- Sender's username
    (SELECT username FROM users WHERE users.id = messages.receiver_id) AS receiver_username -- Receiver's username
FROM messages
WHERE 
    (messages.sender_id = ? AND messages.receiver_id = ?) -- Messages from sender to receiver
    OR 
    (messages.sender_id = ? AND messages.receiver_id = ?) -- Messages from receiver to sender
ORDER BY messages.timestamp ASC;
    ''', sender_id, receiver_id, receiver_id, sender_id)

    return render_template('direct.html', messages=messages, receiver=receiver)
