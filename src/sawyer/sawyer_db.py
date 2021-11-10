import sqlite3 as sql

connection  = sql.connect('sawyer.db')
cursor = connection.cursor()
scriptFile = open('./initdb.sql', 'r')
script = scriptFile.read()
scriptFile.close()
cursor.executescript(script)
connection.commit()