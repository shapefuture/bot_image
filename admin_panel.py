# -*- coding: utf-8 -*-
import os

from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask import Flask, redirect, url_for, request, render_template
from flask_admin import Admin, AdminIndexView, form, expose, BaseView
from flask_admin.contrib.peewee import ModelView

import sqldb


def get_admin_password():
    with open(os.getcwd() + "/admin/credentials.txt", encoding='utf8') as file:
        password = file.read()
    return password


def update_admin_password(new_password):
    with open(os.getcwd() + "/admin/credentials.txt", mode="w", encoding='utf8') as file:
        file.write(new_password)


app_admin = Flask(__name__)
app_admin.config["SECRET_KEY"] = "LAMBDA"
app_admin.config["FLASK_ADMIN_SWATCH"] = 'cerulean'


class ProtectedModelView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated


class ProtectedBaseView(BaseView):
    def is_accessible(self):
        return current_user.is_authenticated


class UserModelView(ProtectedModelView):
    can_export = True
    column_searchable_list = ['interval']


class UpdatePasswordView(ProtectedBaseView):
    @expose('/', methods=('GET', 'POST'))
    def update_password_page(self):
        if request.method == "POST":
            new_password = request.form.get("password")
            update_admin_password(new_password)
        return self.render("update_password.html")


admin = Admin(app_admin, name='Productivity Bot', template_mode="bootstrap4", index_view=AdminIndexView(url='/admin'))
admin.add_view(ProtectedModelView(sqldb.User, name="Пользователи"))
admin.add_view(UserModelView(sqldb.Settings, name="Настройки"))
admin.add_view(UserModelView(sqldb.Images, name="Изображения"))
admin.add_view(UserModelView(sqldb.Notifications, name="Уведомления"))
admin.add_view(UserModelView(sqldb.Intervals, name="Интервалы"))
admin.add_view(UpdatePasswordView(name="Пароль", endpoint="password"))

login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app_admin)


class User(UserMixin):
    def __init__(self, id):
        self.id = id

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)


# Login route
@app_admin.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == 'admin' and password == get_admin_password():  # Replace with your authentication logic
            user = User(1)
            login_user(user)
            return redirect(url_for('admin.index'))
    return render_template('login.html')


@app_admin.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app_admin.before_request
def before_request():
    if not current_user.is_authenticated and request.endpoint in ('admin.index', 'admin'):
        return redirect(url_for('login'))


@app_admin.get('/')
def index():
    return redirect(url_for('login'))


def run():
    app_admin.run(host='0.0.0.0', port=80)
