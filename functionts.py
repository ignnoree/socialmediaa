from flask import Flask, request, redirect, render_template,session,flash,jsonify
from werkzeug.security import generate_password_hash,check_password_hash
from cs50 import SQL

from profilequery import profile_query,home_query

db=SQL('sqlite:///mydatabase.db')


def ifpost_contents(username,action):
    if action=='create_post':
        content=request.form.get('content')
        db.execute('insert into posts(content,username) VALUES (?,?)',content,username)

    elif action=='post_comment':
        
        comment_content=request.form.get('comment_content')
        post_id=request.form.get('post_id')
        
        if comment_content and post_id:
            db.execute('insert into comments(post_id,content,username) VALUES (?,?,?)',post_id,comment_content,username)

    elif action=='delete_comment':
        commentid=request.form.get('comment_id')
        if commentid and username:
            db.execute('delete from comments where id = ? and username = ?',commentid,username)

    elif action=='delete_post':
        post_id=request.form.get('post_id')
        if post_id:
            db.execute('DELETE FROM posts WHERE id = ? AND username = ?', post_id, username)

    elif action =='like_post' :
        post_id=request.form.get('post_id')
        existing_likes=db.execute('select * from likes where author = ? and post_id=?',username,post_id)
        if not existing_likes : 
            db.execute('insert into likes (author,post_id) values (?,?)',username,post_id)
            
        else:
            db.execute('delete from likes where post_id = ? and author = ?',post_id,username)
            
    elif request.method == 'PUT':
        new_postid=request.json.get('post_id')
        postcontent=request.json.get('edited_content')
        db.execute('update posts set content = ? where id = ?',postcontent,new_postid)
    



def getusername(user_id):
    user = db.execute('SELECT username FROM users WHERE id = ?', (user_id,))
    if user:
        return user[0]['username']

