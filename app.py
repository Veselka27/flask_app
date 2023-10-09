from flask import Flask, request, render_template, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
import requests, datetime, json, bcrypt

app = Flask(__name__, template_folder="assets")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = "1234567890"
app.app_context().push()
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    passwd = db.Column(db.String(80), nullable=False)
    buttoncount = db.Column(db.Integer)
    visitcount = db.Column(db.Integer)

    def __init__(self, username, passwd, buttoncount, visitcount):
        self.username = username
        self.passwd = passwd
        self.buttoncount = buttoncount
        self.visitcount = visitcount


quote_url: str = "https://favqs.com/api/qotd"
meme_url: str  = "https://meme-api.com/gimme"
path: str = "/home/pi/flask_app/data.json"

def get_quote(url: str):
    response = requests.get(url)
    data: dict = response.json()
    quote = data["quote"]["body"]
    author = data["quote"]["author"]
    return quote, author

def get_meme(url: str):
    try:
        response = requests.get(url)
        data: dict = response.json()
        meme = data["preview"][2]
        return meme, True
    except Exception:
        return None, False

@app.route("/")
def main():
    if "user" in session:
        return render_template("index.html", user=session["user"])
    else:
        return redirect(url_for("login"))
    
@app.route("/login", methods=["POST", "GET"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        passwd = request.form["passwd"]
        usr = User.query.filter_by(username=username).first()
        try:
            if usr.username == username and bcrypt.checkpw(passwd.encode('utf-8'), usr.passwd): # type: ignore
                session["user"] = username
                return redirect(url_for("main"))
            else:
                return render_template("login.html", message="Wrong username or password!")
        except AttributeError:
            return render_template("login.html", message="This username doesn't exist!")
    else:
        return render_template("login.html")

@app.route("/signin", methods=["POST", "GET"])
def signin():
    if request.method == "POST":
        username = request.form["username"]
        passwd = request.form["passwd"]
        hashed_passwd = bcrypt.hashpw(passwd.encode('utf-8'), bcrypt.gensalt())
        usr = User.query.filter_by(username=username).first()
        if usr:
            return render_template("signin.html", message="This account already exists!")
        else:
            new_usr = User(username=username, passwd=hashed_passwd, buttoncount=0, visitcount=0)
            db.session.add(new_usr)
            db.session.commit()
            return redirect(url_for("main"))
    else:
        return render_template("signin.html")

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("main"))

@app.route("/button-counter", methods=["POST", "GET"])
def button_counter():
    if "user" in session:
        usr = User.query.filter_by(username=session["user"]).first()
        count = usr.buttoncount # type: ignore
        if request.method == "POST":
            usr.buttoncount = count + 1 # type: ignore
            db.session.commit()
            return str(count+1)
        else:
            return render_template("button_counter.html", count=count)
    else:
        return redirect(url_for("main"))

@app.route("/visit-counter")
def visit_counter():
    if "user" in session:
        usr = User.query.filter_by(username=session["user"]).first()
        count = usr.visitcount + 1 # type: ignore
        usr.visitcount = count # type: ignore
        db.session.commit()
        return render_template("visit_counter.html", count=count)
    else:
        return redirect(url_for("main"))

@app.route("/quote-of-the-day")
def quote_of_the_day():
    if "user" in session:
        quote, author = get_quote(quote_url)
        return render_template("quote_of_the_day.html", quote=quote, author=author)
    else:
        return redirect(url_for("main"))

@app.route("/meme")
def meme():
    if "user" in session:
        meme, success = get_meme(meme_url)
        if success:
            return render_template("meme.html", meme=meme, meme_title="Meme:")
        else:
            return render_template("meme.html", meme=meme, meme_title="Something went wrong")
    else:
        return redirect(url_for("main"))

@app.route("/tip-calculator")
def tip_calculator():
    if "user" in session:
        return render_template("tip-calculator.html")
    else:
        return redirect(url_for("main"))

@app.route("/testing", methods=["POST", "GET"])
def testing():
        if request.method == "POST":
            usr = User.query.all()
        else: 
            usr = "not found"
        return render_template('test.html')

if __name__ == '__main__':
    app.run(host="0.0.0.0")