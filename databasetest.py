from cs50 import SQL

db=SQL('sqlite:///mydatabase.db')
db.execute('insert into posts(id,user_id,content)VALUES(?,?,?)','test','test','test')