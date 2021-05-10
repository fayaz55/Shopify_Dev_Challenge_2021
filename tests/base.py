import os
import unittest
import mysql.connector
from flask_mysqldb import MySQL
from ..app import app
     
from passlib.handlers.sha2_crypt import sha256_crypt


class BaseTestCase(TestCase):
    """A base test case."""

    def create_app(self):
        app.config.from_object('config.TestConfig')
        return app

    def setUp(self):
        # Config MySQL
        app.config['MYSQL_HOST'] = 'localhost'
        app.config['MYSQL_USER'] = 'root'
        app.config['MYSQL_PASSWORD'] = 'password'
        app.config['MYSQL_DB'] = 'myflaskapp'
        app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

        # init MYSQL
        mysql = MySQL(app)
        
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO users(name, email, username, password) VALUES(%s, %s, %s, %s)", ("test", "test@email.com", "test", sha256_crypt.encrypt("test")))
         # Commit to DB
        mysql.connection.commit()
        
        # Close connection
        cur.close()

        # Create user directory to store file images
        new_path=os.path.join(app.config['UPLOADS'],"test")
        os.mkdir(new_path)

    def tearDown(self):
        pass