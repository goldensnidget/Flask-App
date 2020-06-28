from flask import Flask, render_template, flash, redirect, url_for, session, logging, request
#from data import Posts
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from functools import wraps
from passlib.hash import sha256_crypt

app = Flask(__name__)

# config mysql
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '14@Anjumanju'
app.config['MYSQL_DB'] = 'helpforum'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
mysql = MySQL(app)

#Posts = Posts()

@app.route('/')
def index():
	return render_template('home.html')

@app.route('/about')
def about():
	return render_template('about.html')

@app.route('/posts')
def posts():
	cur = mysql.connection.cursor()

	result = cur.execute("SELECT * FROM posts")

	posts = cur.fetchall()

	if result > 0:
		return render_template('posts.html', posts=posts)
	else:
		msg = 'No Posts Found'
		return render_template('posts.html', msg=msg)

	cur.close()

@app.route('/post/<string:id>/')
def post(id):
	cur = mysql.connection.cursor()

	result = cur.execute("SELECT * FROM posts WHERE id = %s", [id])

	post = cur.fetchone()

	return render_template('post.html', post=post)

class RegisterForm(Form):
	name = StringField('Name', [validators.Length(min=1, max=50)])
	username = StringField('Username', [validators.Length(min=4, max=25)])
	email = StringField('Email', [validators.Length(min=6, max=50)])
	password = PasswordField('Password', [
		validators.DataRequired(), 
		validators.EqualTo('confirm', message='Passwords do not match')
		])
	confirm = PasswordField('Confirm Password')

@app.route('/register', methods=['GET', 'POST'])
def register():
	form = RegisterForm(request.form)
	if request.method == 'POST' and form.validate():
		name = form.name.data
		email = form.email.data
		username = form.username.data
		password = sha256_crypt.encrypt(str(form.password.data))

		cur = mysql.connection.cursor()

		cur.execute("INSERT INTO users(name, email, username, password) VALUES(%s, %s, %s, %s)", (name, email, username, password))

		mysql.connection.commit()

		cur.close()

		flash('You are now registered and can login', 'success')

		return redirect(url_for('index'))
	return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
	if request.method == 'POST':
		username = request.form['username']
		password_candidate = request.form['password']

		cur = mysql.connection.cursor()

		result = cur.execute("SELECT *FROM users WHERE username = %s", [username])

		if result > 0:
			data = cur.fetchone()
			password = data['password']

			if sha256_crypt.verify(password_candidate, password):
				session['logged_in'] = True
				session['username'] = username

				flash('You are now logged in', 'success')
				return redirect(url_for('dashboard'))
			else:
				error = 'Invalid login'
				return render_template('login.html', error=error)
			
			cur.close()

		else:
			error = 'Username not found'
			return render_template('login.html', error)

	return render_template('login.html')

def is_logged_in(f):
	@wraps(f)
	def wrap(*args, **kwargs):
		if 'logged_in' in session:
			return f(*args, **kwargs)
		else:
			flash('Unauthorized, Please login', 'danger')
			return redirect(url_for('login'))
	return wrap

@app.route('/logout')
def logout():
	session.clear()
	flash('You are now logged out', 'success')
	return redirect(url_for('login'))

@app.route('/dashboard')
@is_logged_in
def dashboard():

	cur = mysql.connection.cursor()

	result = cur.execute("SELECT * FROM posts")

	posts = cur.fetchall()

	if result > 0:
		return render_template('dashboard.html', posts=posts)
	else:
		msg = 'No Posts Found'
		return render_template('dashboard.html', msg=msg)

	cur.close()

class PostForm(Form):
	title = StringField('Title', [validators.Length(min=1, max=50)])
	body = TextAreaField('Body', [validators.Length(min=30)])


@app.route('/add_post', methods=['GET', 'POST'])
@is_logged_in
def add_post():
	form = PostForm(request.form)
	if request.method == 'POST' and form.validate():
		title = form.title.data
		body = form.body.data

		cur = mysql.connection.cursor()

		cur.execute("INSERT INTO posts(title, body, user) VALUES(%s, %s, %s)", (title, body, session['username']))

		mysql.connection.commit()

		cur.close()

		flash('Post Created', 'success')

		return redirect(url_for('dashboard'))

	return render_template('add_post.html', form=form)

@app.route('/edit_post/<string:id>', methods=['GET', 'POST'])
@is_logged_in
def edit_post(id):

	cur = mysql.connection.cursor()

	result = cur.execute("SELECT * FROM posts WHERE id = %s", [id])

	post = cur.fetchone()

	form = PostForm(request.form)

	form.title.data = post['title']
	form.body.data = post['body']

	if request.method == 'POST' and form.validate():
		title = request.form['title']
		body = request.form['body']

		cur = mysql.connection.cursor()

		cur.execute("UPDATE posts SET title=%s, body=%s WHERE id = %s", (title, body, id))

		mysql.connection.commit()

		cur.close()

		flash('Post Updated', 'success')

		return redirect(url_for('dashboard'))

	return render_template('edit_post.html', form=form)

@app.route('/delete_post/<string:id>', methods=['POST'])
@is_logged_in
def delete_post(id):

	cur = mysql.connection.cursor()

	cur.execute("DELETE FROM posts WHERE id = %s", [id])
	mysql.connection.commit()

	cur.close()
	flash('Post Deleted', 'success')

	return redirect(url_for('dashboard'))


if __name__ == '__main__':
	app.secret_key='secret123'
	app.run(debug=True)



