from flask import Flask, render_template, flash, redirect, url_for, session, request, logging, send_from_directory
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from flask_wtf.file import FileField, FileRequired
from passlib.hash import sha256_crypt
from functools import wraps
from werkzeug.utils import secure_filename
import mysql.connector
import os


app = Flask(__name__)
app.secret_key='secret'
# Config MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'password'
app.config['MYSQL_DB'] = 'myflaskapp'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

# init MYSQL
mysql = MySQL(app)

app.config['UPLOADS']='uploads/'  # Directory where images will be stored
app.config['ALLOWED_IMAGE_EXTENSIONS'] = ['JPEG', 'JPG', 'PNG', 'GIF']



# Index
@app.route('/')
def index():

    #Create Cursor
    cur = mysql.connection.cursor()
    #Create tables in MYSQL
    cur.execute("CREATE TABLE IF NOT EXISTS users (username VARCHAR(30) PRIMARY KEY, name VARCHAR(100), email VARCHAR(100), password VARCHAR(100), reg_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP);")
    cur.execute("CREATE TABLE IF NOT EXISTS gallery(id INT (11) AUTO_INCREMENT PRIMARY KEY, photo_name VARCHAR(250), username VARCHAR(30) REFERENCES users(username), privacy TINYINT(1),ul_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP);")

    mysql.connection.commit()

    # Retrieve all public images from database
    result = cur.execute("SELECT * FROM gallery WHERE privacy=0 ORDER BY ul_date DESC")
    articles = cur.fetchall()
    if result > 0:
        return render_template('home.html', articles=articles)

    return render_template('home.html')



# Register Form Class
class RegisterForm(Form):
    name = StringField('Name', [validators.Length(min=1, max=50)])
    username = StringField('Username', [validators.Length(min=4, max=25)])
    email = StringField('Email', [validators.Length(min=6, max=50)])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords do not match')
    ])
    confirm = PasswordField('Confirm Password')


# Register User
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))

        # Create cursor
        cur = mysql.connection.cursor()

        # Check if Username exists already. Else, Create user.
        result =cur.execute('SELECT * FROM users WHERE username= %s', [username])
        if result>0:
            flash('Error: Username Exists')
            return redirect(url_for('register'))
        else:
            # Execute query
            cur.execute("INSERT INTO users(name, email, username, password) VALUES(%s, %s, %s, %s)", (name, email, username, password))
            
            # Commit to DB
            mysql.connection.commit()
            
            # Close connection
            cur.close()

            # Create user directory to store file images
            new_path=os.path.join(app.config['UPLOADS'],username)
            os.mkdir(new_path)

            flash('You are now registered and can log in', 'success')
        
        return redirect(url_for('login'))

    return render_template('register.html', form=form)


# User login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Get Form Fields
        username = request.form['username']
        password_candidate = request.form['password']

        # Create cursor
        cur = mysql.connection.cursor()

        # Get user by username
        result = cur.execute("SELECT * FROM users WHERE username = %s", [username])

        if result > 0:
            # Get stored hash
            data = cur.fetchone()
            password = data['password']

            # Compare Passwords
            if sha256_crypt.verify(password_candidate, password):
                # Passed
                session['logged_in'] = True
                session['username'] = username

                flash('You are now logged in', 'success')
                return redirect(url_for('dashboard'))
            else:
                error = 'Invalid login'
                return render_template('login.html', error=error)
            # Close connection
            cur.close()
        else:
            error = 'Username not found'
            return render_template('login.html', error=error)

    return render_template('login.html')

# Check if user logged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please login', 'danger')
            return redirect(url_for('login'))
    return wrap


# Dashboard
@app.route('/dashboard')
@is_logged_in
def dashboard():
    # Create cursor
    cur = mysql.connection.cursor()

    # Show images only from the user logged in 
    result = cur.execute("SELECT * FROM gallery WHERE username = %s ORDER BY ul_date DESC", [session['username']])
    articles = cur.fetchall()

    if result > 0:
        return render_template('dashboard.html', articles=articles)
    else:
        msg = 'No Articles Found'
        return render_template('dashboard.html', msg=msg)
    # Close connection
    cur.close()

# Logout
@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash('You are now logged out', 'success')
    return redirect(url_for('login'))



def allowed_image(filename):
    
    # We only want files with a . in the filename
    if not "." in filename:
        return False

    # Split the extension from the filename
    ext = filename.rsplit(".", 1)[1]

    # Check if the extension is in ALLOWED_IMAGE_EXTENSIONS
    if ext.upper() in app.config["ALLOWED_IMAGE_EXTENSIONS"]:
        return True
    else:
        return False

# For Multiple images
def allowed_size(image):
    # Check if the image does not exceed Max FileSize of 5MB
    image.seek(0,os.SEEK_END)
    file_length=image.tell()
    image.seek(0)

    if file_length>=5*1024*1024:  #5MB Max FileSize:
        return False
    else:
        return True
 
# Upload Pictures
@app.route('/upload' , methods= ["GET", "POST"] )
@is_logged_in
def upload():
    if request.method == "POST":
        
        if request.files:
            privacy=int(request.form["visibility"])
            image=request.files["image"]
            filesize=int(request.content_length)

            if filesize> 5*1024*1024:    #5MB FILESIZE LIMIT
                flash('File is TOO DAMN LARGE!! 5MB MAX.')
                return redirect(url_for('upload'))

            if image.filename == "":
                flash("No filename")
                return redirect(url_for('upload'))

            if (allowed_image(image.filename)):
                filename=secure_filename(image.filename)
                image.save(os.path.join(app.config['UPLOADS'],session['username'], filename))
                cur = mysql.connection.cursor()
                cur.execute("INSERT INTO gallery(photo_name,username,privacy) Values (%s,%s,%s)", (filename, session['username'], privacy)) 
                mysql.connection.commit()
                cur.close()
            else:
                flash('INVALID FILE TYPE')
                return redirect(url_for('upload'))

            return redirect(url_for('dashboard'))


            # Code for Multiple Images Partially Working

            # privacy=int(request.form["visibility"])
            # # Check for any errors that might occur
            # for f in request.files.getlist('image'):
            #     if f.filename == "":
            #         flash("Error: One or more files have no filename")
            #         return redirect(url_for('upload'))
            #     if not allowed_image(f.filename):
            #         flash('Error: One or more files have an invalid file type')
            #         return redirect(url_for('upload'))
            #     if not allowed_size(f):
            #         flash('Error: One or more files have exceeded limit. Max file size is 5MB')
            #         return redirect(url_for('upload'))

            # # Store image name into MySQL and the image itself into the filesystem
            # for f in request.files.getlist('image'):
                
            #     image_name=secure_filename(f.filename)

            #     # Store image name into MySQL                
            #     cur = mysql.connection.cursor()

            #     result =cur.execute('SELECT * FROM gallery WHERE photo_name= %s and username=%s', (image_name,session['username']))
            #     if result>0:
            #         flash('Error: One or more file names already exist in repository')
            #         return redirect(url_for('upload'))
                
            #     cur.execute("INSERT INTO gallery(photo_name,username,privacy) Values (%s,%s,%s)", (image_name, session['username'], privacy)) 
            #     mysql.connection.commit()
            #     cur.close()
                
            #     # Store image into File System
            #     f.save(os.path.join(app.config['UPLOADS'],session['username'], image_name))
            #     flash('Success! File(s) have been uploaded')

            #     return redirect(url_for('dashboard'))


    return render_template("upload.html")

# Display Image
@app.route('/displayimage/<filename>')
@is_logged_in
def displayimage(filename):
    image_dir=os.path.join(app.config['UPLOADS'],session['username'])
    return send_from_directory(image_dir, filename)

# Delete Image
@app.route('/delete_article/<string:id>', methods=['POST'])
@is_logged_in
def delete_article(id):
    location=os.path.join(app.config["UPLOADS"],session['username'],id)
    os.remove(location)
    # Create cursor
    cur = mysql.connection.cursor()
    # Execute
    cur.execute("DELETE FROM gallery WHERE username = %s and photo_name=%s", (session['username'],id))
    # Commit to DB
    mysql.connection.commit()
    #Close connection
    cur.close()

    flash('Image Deleted', 'success')

    return redirect(url_for('dashboard'))

# Image Form Class
class ImageForm(Form):
    filename = StringField('File Name', [validators.Length(min=1, max=200)])
    file_type= StringField('File Type', render_kw={'readonly': True})

#Edit Image
@app.route('/edit_image/<string:id>', methods=['GET', 'POST'])
@is_logged_in
def edit_image(id):
    # Create cursor
    cur = mysql.connection.cursor()

    # Get article by id
    result = cur.execute("SELECT * FROM gallery WHERE id = %s", [id])
    article = cur.fetchone()
    cur.close()

    form = ImageForm(request.form)
    ext = article['photo_name'].rsplit(".",1)

    form.filename.data = ext[0]
    form.file_type.data = "." + ext[1]

    if request.method == 'POST' and form.validate():
        #Retrieve Data From Form
        privacy = int(request.form['visibility'])
        edited_filename = request.form['filename'] + "." + ext[1]
        edited_filename=secure_filename(edited_filename)

        # Create Cursor
        cur = mysql.connection.cursor()

        result =cur.execute('SELECT * FROM gallery WHERE photo_name= %s and username=%s and id<>%s', (edited_filename,article['username'],id))
        if result>0:
            flash('Error: Filename Exists')
            return redirect(url_for('edit_image',id=id))
        # Execute
        cur.execute ("UPDATE gallery SET photo_name=%s, privacy=%s WHERE id=%s",(edited_filename, privacy, id))
        # Commit to DB
        mysql.connection.commit()
        #Close connection
        cur.close()

        old_dir=os.path.join(app.config['UPLOADS'],session['username'],article['photo_name'])
        new_dir=os.path.join(app.config['UPLOADS'],session['username'],edited_filename)
        os.rename(old_dir,new_dir)

        flash('Image Updated')

        return redirect(url_for('dashboard'))

    return render_template('edit_image.html', form=form)

if __name__ == '__main__':
    app.secret_key='secret123'
    app.run()