
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy

from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user #AI

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
# /// = relative path, //// = absolute path
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

  # Needed for session management and flash messages#AI

db = SQLAlchemy(app)

#Add
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    database_uri = db.Column(db.String(200), nullable=False) #Additional

class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    complete = db.Column(db.Boolean)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.before_request
def before_request():
    if current_user.is_authenticated:
        # Set the database URI to the user's specific database
        app.config['SQLALCHEMY_DATABASE_URI'] = current_user.database_uri
        db.engine.dispose()  # Dispose of the current engine to use the new URI
        db.create_all()  # Ensure the database is created


@app.route("/")
@login_required
def home():
    todo_list = Todo.query.filter_by(user_id=current_user.id).all()
    return render_template("base.html", todo_list=todo_list)  
    
    
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        existing_user = User.query.filter_by(username=username).first()
        # existing_password = User.query.filter_by(password=password).first()
        if existing_user:
            flash("Username already exists.", "error")
        # elif existing_password:
            # flash("Password already exists.", "error")
        else:
            # Generate a unique database URI for the new user
            database_uri = f'sqlite:///db_{username}.sqlite' #Additional
            # user = User(username=username, password=password)
            user = User(username=username, password=password, database_uri=database_uri)#Additional
            db.session.add(user)
            db.session.commit()
            flash("Signup successful! Please login.", "success")
            return redirect(url_for("login"))
    return render_template("signup.html") 
    


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user = User.query.filter_by(username=username).first()
        if user and user.password == password:
            login_user(user)
            return redirect(url_for("home"))
        else:
            flash("Invalid username or password")
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

@app.route("/add", methods=["POST"])
@login_required
def add():
    title = request.form.get("title")
    new_todo = Todo(title=title, complete=False,user_id=current_user.id)
    db.session.add(new_todo)
    db.session.commit()
    return redirect(url_for("home"))


@app.route("/update/<int:todo_id>")
@login_required
def update(todo_id):
    todo = Todo.query.filter_by(id=todo_id, user_id=current_user.id).first()
    if todo:
        todo.complete = not todo.complete
        db.session.commit()
    return redirect(url_for("home"))


@app.route("/delete/<int:todo_id>")
@login_required
def delete(todo_id):
    todo = Todo.query.filter_by(id=todo_id, user_id=current_user.id).first()
    if todo:
        db.session.delete(todo)
        db.session.commit()
    return redirect(url_for("home"))

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)