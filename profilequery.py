profile_query='''SELECT posts.id AS post_id, 
       posts.username AS post_author, 
       posts.content AS post_content, 
       posts.created_at AS post_created_at, 
       comments.id AS comment_id, 
       comments.content AS comment_content, 
       comments.username AS comment_author   
FROM posts
LEFT JOIN comments ON posts.id = comments.post_id
WHERE posts.username = ?
ORDER BY posts.created_at DESC'''
 

home_query='''
select posts.id as post_id,
 posts.username as posts_author,
 posts.content as posts_content,
 posts.created_at as post_created_at,
 comments.id as comment_id,
 comments.username as comment_author,
 comments.content as comment
FROM posts 
left join comments on posts.id = comments.post_id
inner join users on posts.username = users.username
inner join followers on users.id=followers.followed_id
where followers.follower_id= ?
ORDER BY 
    posts.created_at DESC;
'''
