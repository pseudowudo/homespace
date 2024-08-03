from flask import Flask, render_template, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length, ValidationError,DataRequired
from flask_bcrypt import Bcrypt
from requests import get
from datetime import datetime

app = Flask(__name__)
db=SQLAlchemy()
bcrypt=Bcrypt(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SECRET_KEY']='thisismysecretkey'
db.init_app(app)



login_manager=LoginManager()
login_manager.init_app(app)
login_manager.login_view="login"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id=db.Column(db.Integer, primary_key=True)
    username =db.Column(db.String(20),nullable=False, unique=True)
    password =db.Column(db.String(80),nullable=False)
    todos=db.relationship('Todo',backref='author',lazy=True)

class Todo(db.Model,UserMixin):
    id=db.Column(db.Integer,primary_key=True)
    title=db.Column(db.String(100),nullable=False)
    date_posted=db.Column(db.DateTime,nullable=False,default=datetime.utcnow)
    taskdone=db.Column(db.String(20),nullable=False,default="No")
    user_id=db.Column(db.Integer,db.ForeignKey('user.id'),nullable=False)
    
    def __repr__(self):
        return f"Todo('{self.title}','{self.date_posted}')"
    

class RegisterForm(FlaskForm):
    username=StringField(validators=[InputRequired(),Length(min=4,max=20)])
    password= PasswordField(validators=[InputRequired(),Length(min=4,max=20)])
    submit = SubmitField("Register")

    def validate_username(self, username):
        existing_user_username=User.query.filter_by(
            username=username.data).first()

        if existing_user_username:
            raise ValidationError(
                "Username already Exists!")

class LoginForm(FlaskForm):
    username=StringField(validators=[InputRequired(),Length(min=4,max=20)],render_kw={"placeholder":"Username"})
    password= PasswordField(validators=[InputRequired(),Length(min=4,max=20)],render_kw={"placeholder":"Password"})
    submit = SubmitField("Login")
class PostForm(FlaskForm):
    title=StringField('Title',validators=[DataRequired()])
    submit=SubmitField('Add')
    
@app.route("/")
def home():
    return render_template("home.html")


@app.route("/login",methods=['GET','POST'])
def login():
    form=LoginForm()
    if form.validate_on_submit():
        user=User.query.filter_by(username=form.username.data).first()
        if user:
            if bcrypt.check_password_hash(user.password,form.password.data):
                login_user(user)
                return redirect(url_for('dashboard'))
    return render_template("login.html",form=form)

@app.route("/logout",methods=['GET','POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))



@app.route("/register",methods=['GET','POST'])
def register():
    form=RegisterForm()
    if form.validate_on_submit():
        hashed_password=bcrypt.generate_password_hash(form.password.data)
        new_user=User(username=form.username.data,password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template("register.html",form=form)

@app.route("/dashboard",methods=['GET','POST'])
@login_required
def dashboard():

    todois=Todo.query.all()

    ip = get('https://api.ipify.org').text
    ip=str(ip)
    base_url = 'http://api.weatherapi.com/v1/current.json?key=5ac064a2eac8458daf292026240307&q='
    url = ''.join([base_url, ip])
    response = get(url)
    weather_data = response.json()
    temp=weather_data['current']['temp_c']
    day=weather_data['current']['is_day']
    wdata=weather_data['current']['condition']['text']
    loc1=weather_data['location']['name']
    loc2=weather_data['location']['region']

    form=PostForm()
    if form.validate_on_submit():
        new_post=Todo(title=form.title.data,author=current_user)
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for('dashboard'))
    
    
    
    if day==1:
        return render_template('dashday.html',temp=temp,wdata=wdata,username=current_user.username,ids=current_user.id,loc1=loc1,loc2=loc2,todois=todois,form=form,ip=ip)

    if day==0:
        return render_template('dashnight.html',temp=temp,wdata=wdata,username=current_user.username,ids=current_user.id,loc1=loc1,loc2=loc2,todois=todois,form=form,ip=ip)