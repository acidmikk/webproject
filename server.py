import sqlite3
from flask import *
from add_news import AddNewsForm

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, \
    SelectField, RadioField
from wtforms.validators import DataRequired
from flask import redirect, flash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'


class DB:
    def __init__(self):
        conn = sqlite3.connect('news.db', check_same_thread=False)
        self.conn = conn

    def get_connection(self):
        return self.conn

    def __del__(self):
        self.conn.close()


db = DB()


class UsersModel:
    def __init__(self, connection):
        self.connection = connection

    def init_table(self):
        cursor = self.connection.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                            (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                             user_name VARCHAR(50),
                             password_hash VARCHAR(128)
                             )''')
        cursor.close()
        self.connection.commit()

    def insert(self, user_name, password_hash):
        cursor = self.connection.cursor()
        if not cursor.execute("SELECT * FROM users WHERE "
                          "user_name = ?", (str(user_name),)).fetchone():
            cursor.execute('''INSERT INTO users 
                              (user_name, password_hash) 
                              VALUES (?,?)''', (user_name, password_hash,))
        cursor.close()
        self.connection.commit()

    def get(self, user_id):
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (str(user_id),))
        row = cursor.fetchone()
        return row

    def get_all(self):
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM users")
        rows = cursor.fetchall()
        return rows

    def exists(self, user_name, password_hash):
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM users WHERE user_name = ? AND password_hash = ?",
                       (user_name, password_hash))
        row = cursor.fetchone()
        return (True, row[0]) if row else (False,)

    def get_id(self, user_name):
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM users WHERE user_name = ?", (str(user_name),))
        row = cursor.fetchone()
        return row[0]

UsersModel(db.get_connection()).init_table()


class NewsModel:
    def __init__(self, connection):
        self.connection = connection

    def init_table(self):
        cursor = self.connection.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS news 
                            (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                             title VARCHAR(100),
                             content VARCHAR(1000),
                             user_id INTEGER,
                             user_name VARCHAR(50)
                             )''')
        cursor.close()
        self.connection.commit()

    def insert(self, title, content, user_id, user_name):
        cursor = self.connection.cursor()
        cursor.execute('''INSERT INTO news 
                          (title, content, user_id, user_name) 
                          VALUES (?,?,?,?)''', (title, content, str(user_id), user_name))
        cursor.close()
        self.connection.commit()

    def get(self, news_id):
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM news WHERE id = ?", (str(news_id),))
        row = cursor.fetchone()
        return row

    def get_all(self, user_id=None):
        cursor = self.connection.cursor()
        if user_id:
            cursor.execute("SELECT * FROM news WHERE user_id = ?",
                           (str(user_id),))
        else:
            cursor.execute("SELECT * FROM news")
        rows = cursor.fetchall()
        return rows

    def delete(self, news_id):
        cursor = self.connection.cursor()
        cursor.execute('''DELETE FROM news WHERE id = ?''', (str(news_id),))
        cursor.close()
        self.connection.commit()


NewsModel(db.get_connection()).init_table()


class LoginForm(FlaskForm):
    username = StringField('Логин', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')


class NewsList(FlaskForm):
    sort = SelectField('Сортировка по', choices=[('time', 'По времени добавления'),
                                                 ('alph', 'По алфавиту')])
    poryadok = RadioField('', choices=[('down', 'По убыванию'), ('up', 'По возрастанию')])
    submit = SubmitField('Показать')


@app.route('/')
@app.route('/index', methods=['GET', 'POST'])
def index():
    form = NewsList()
    if 'username' not in session:
        return redirect('/login')
    if form.validate_on_submit():
        news = list(NewsModel(db.get_connection()).get_all(session['user_id']))
        sortd = form.sort.data
        por = form.poryadok.data
        if sortd == 'alph':
            news = sorted(news, key=lambda x: x[1])
        if por == 'down':
            news = reversed(news)
        return render_template('index.html', username=session['username'],
                           news=news, form=form)
    news = reversed(list(NewsModel(db.get_connection()).get_all(session['user_id'])))
    print(news)
    return render_template('index.html', username=session['username'],
                           news=news, form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    user_name = form.username.data
    password = form.password.data
    user_model = UsersModel(db.get_connection())
    exists = user_model.exists(user_name, password)
    if (exists[0]):
        session['username'] = user_name
        session['user_id'] = exists[1]
        return redirect("/index")
    return render_template('login.html', title='Авторизация', form=form)


@app.route('/logout')
def logout():
    session.pop('username',0)
    session.pop('user_id',0)
    return redirect('/login')


@app.route('/add_news', methods=['GET', 'POST'])
def add_news():
    if 'username' not in session:
        return redirect('/login')
    form = AddNewsForm()
    if form.validate_on_submit():
        title = form.title.data
        content = form.content.data
        nm = NewsModel(db.get_connection())
        nm.insert(title, content, session['user_id'], session['username'])
        return redirect("/index")
    return render_template('add_news.html', title='Добавление новости',
                           form=form, username=session['username'])


@app.route('/delete_news/<int:news_id>', methods=['GET'])
def delete_news(news_id):
    if 'username' not in session:
        return redirect('/login')
    nm = NewsModel(db.get_connection())
    print(nm.get(news_id))
    if nm.get(news_id)[3] == session['user_id'] or session['username'] == 'admin':
        nm.delete(news_id)
    return redirect("/index")


@app.route('/register', methods=['GET', 'POST'])
def reg():
    form = LoginForm()
    if form.validate_on_submit():
        user_name = form.username.data
        password = form.password.data
        user_model = UsersModel(db.get_connection())
        user_model.insert(user_name, password)
        return redirect('/login')
    return render_template('/register.html', form=form, title='Регистрация')


@app.route('/users', methods=['GET', 'POST'])
def users():
    if session['username'] != 'admin':
        pass
    users_list = UsersModel(db.get_connection()).get_all()
    usersn = []
    for i in users_list:
        usernews = len(NewsModel(db.get_connection()).get_all(i[0]))
        usersn.append(((i[1]), usernews))
    return render_template('/users.html', users=usersn)


@app.route('/user/<username>', methods=['GET', 'POST'])
def user(username):
    userid = UsersModel(db.get_connection()).get_id(username)
    usernews = NewsModel(db.get_connection()).get_all(userid)
    return render_template('user.html', username=username, news=usernews)


if __name__ == '__main__':
    app.run(port=8080, host='127.0.0.1')