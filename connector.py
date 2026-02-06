import mysql.connector

mydb = mysql.connector.connect(
    host='localhost',
    user='root',
    password='Lisbon67!',
    port='3306',
    database='environment'
)
mycursor = mydb.cursor()

mycursor.execute('SELECT * FROM users')

users = mycursor.fetchall()

for user in users:
    print(user)
    print('username ' + user[1])
    print('password ' + user[2])