from flask import Flask, g, render_template, flash, redirect, url_for, session, logging, request

from flask_mysqldb import MySQL

from wtforms import Form, StringField, TextAreaField, PasswordField, validators

from passlib.hash import sha256_crypt

from functools import wraps

def login_required(f):
    @wraps(f)    
    def decorated_function(*args, **kwargs):
        
        if "logged_in" in session:
            return f(*args, **kwargs)
        
        else:
            flash("Please log in to view dashboard page...","danger")
            return redirect(url_for("login"))
    
    return decorated_function

class RegisterForm(Form):

    name = StringField("Name Surname", validators = [validators.Length(min = 4, max = 25)])
    username = StringField("Username", validators = [validators.Length(min = 4, max = 25)])
    email = StringField("E-mail", validators = [validators.Email(message = "Please enter a valid email address...")])
    password = PasswordField("Password", validators = [
        validators.DataRequired(message = "Please choose a password..."),
        validators.EqualTo(fieldname = "confirm", message = "Password mismatch...")
    ])
    confirm = PasswordField("Verify Password")

class LoginForm(Form):

    username = StringField("User name")
    password = PasswordField("Password")

class ArticleForm(Form):

    title = StringField("Article Title", validators = [validators.Length(min = 5, max = 100)])
    content = TextAreaField("Article Content", validators = [validators.Length(min = 10)])

app = Flask(__name__)

app.secret_key = "aschente"

app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"] = "aschente"
app.config["MYSQL_CURSORCLASS"] = "DictCursor"

mysql = MySQL(app)

@app.route("/")
def index():
    return render_template("index13.html")

@app.route("/about")
def about():
    return render_template("about4.html")

@app.route("/article/<string:id>")
def article(id):
    cursor = mysql.connection.cursor()
    query = "Select * From articles where id = %s"
    result = cursor.execute(query, (id,))

    if result > 0:
        article = cursor.fetchone()
        return render_template("article2.html", article = article)

    else:
        return render_template("article2.html")

@app.route("/articles/<string:id>")
def detail(id):
    return "Articles Id:" + id

@app.route("/dashboard")
@login_required
def dashboard():
    cursor = mysql.connection.cursor()
    query = "Select * From articles where author = %s"
    result = cursor.execute(query, (session["username"],))

    if result > 0:
        articles = cursor.fetchall()
        return render_template("dashboard4.html", articles =articles)

    else:
        return render_template("dashboard4.html")

@app.route("/articles")
def articles():
    cursor = mysql.connection.cursor()
    query = "Select * From articles"
    result = cursor.execute(query)
    if result > 0:
        articles = cursor.fetchall()
        return render_template("articles3.html", articles = articles)
    else:
        return render_template("articles3.html")

@app.route("/delete/<string:id>")
@login_required
def delete(id):
    cursor = mysql.connection.cursor()
    query = "Select * From articles where author = %s and id = %s"
    result = cursor.execute(query, (session["username"], id))

    if result > 0:
        query2 = "Delete from articles where id = %s"
        cursor.execute(query2, (id,))
        mysql.connection.commit()
        return redirect(url_for("dashboard"))

    else:
        flash("No such article exists or you do not have permission to delete the article", "danger")
        return redirect(url_for("index"))

@app.route("/edit/<string:id>", methods = ["GET", "POST"])
@login_required
def update(id):

    if request.method == "GET":
        cursor = mysql.connection.cursor()
        query = "Select * from articles where id = %s and author = %s"
        result = cursor.execute(query,(id, session["username"]))

        if result == 0:
            flash("No such article exists or you do not have permission to delete the article", "danger")
            return redirect(url_for("index"))

        else:
            article = cursor.fetchone()
            form = ArticleForm()
            form.title.data = article["title"]
            form.content.data = article["content"]
            return render_template("update2.html", form = form)

    else:
        form = ArticleForm(request.form)
        newtitle = form.title.data
        newcontent = form.content.data
        query2 = "Update articles Set title = %s, content = %s where id = %s"
        cursor = mysql.connection.cursor()
        cursor.execute(query2, (newtitle, newcontent, id))
        mysql.connection.commit()
        flash("Article successfully update", "success")
        return redirect(url_for("dashboard"))

@app.route("/search", methods = ["GET", "POST"])
def search():

    if request.method == "GET":
        return redirect(url_for("index"))

    else:
        keyword = request.form.get("keyword")
        cursor = mysql.connection.cursor()
        query = "Select * from articles where title like '%" + keyword + "%' "
        result = cursor.execute(query)

        if result == 0:
            flash("No results...","warning")
            return redirect(url_for("articles"))

        else:
            articles = cursor.fetchall()
            return render_template("articles3.html", articles = articles)

@app.route("/login", methods = ["GET", "POST"])
def login():
    form = LoginForm(request.form)

    if request.method == "POST":
        username = form.username.data
        password_entered = form.password.data
        cursor = mysql.connection.cursor()
        query = "Select * From users where username = %s"
        result = cursor.execute(query, (username,))

        if result > 0:
            data = cursor.fetchone()
            real_password = data["password"]

            if sha256_crypt.verify(password_entered, real_password):
                flash("Successfully entered...", "success")
                session["logged_in"] = True
                session["username"] = username
                return redirect(url_for("index"))

            else:
                flash("Wrong password...", "danger")
                return redirect(url_for("login"))

        else:
            flash("Username doesn't exist...", "danger")
            return redirect(url_for("login"))

    else:
        return render_template("login5.html", form = form)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

@app.route("/register", methods = ["GET","POST"])
def register():
    form = RegisterForm(request.form)

    if request.method == "POST" and form.validate():
        name = form.name.data
        username = form.username.data
        email = form.email.data 
        password = sha256_crypt.encrypt(form.password.data) 
        cursor = mysql.connection.cursor() 
        query = "Insert into users(name, email, username, password) VALUES(%s,%s,%s,%s)"
        cursor.execute(query, (name, email, username, password))
        mysql.connection.commit()
        cursor.close()
        flash("Successfully registered","success")
        return redirect(url_for("login"))

    else:
        return render_template("register4.html", form = form)

@app.route("/addarticle", methods = ["GET", "POST"])
def addarticle():
    form = ArticleForm(request.form)

    if request.method == "POST" and form.validate():
        title = form.title.data
        content = form.content.data
        cursor = mysql.connection.cursor()
        query = "Insert into articles(title, author, content) VALUES(%s,%s,%s)"
        cursor.execute(query, (title, session["username"], content))
        mysql.connection.commit()
        cursor.close()
        flash("Article successfully added","success")
        return redirect(url_for("dashboard"))
    
    return render_template("addarticle3.html", form = form)

if __name__ == "__main__":
    app.run(debug = True)
