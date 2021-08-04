import hmac
import sqlite3
import datetime
from flask import Flask, request, jsonify
from flask_jwt import JWT, jwt_required, current_identity
from flask_cors import CORS


class User(object):
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password


def fetch_users():
    with sqlite3.connect('sale.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM user")
        users = cursor.fetchall()

        new_data = []

        for data in users:
            new_data.append(User(data[0], data[3], data[4]))
    return new_data


# TABLE CREATED F0R THE USER REGISTRATION (TABLE 1)
def init_user_table():
    conn = sqlite3.connect('sale.db')
    print("Opened database successfully")

    conn.execute("CREATE TABLE IF NOT EXISTS user(user_id INTEGER PRIMARY KEY AUTOINCREMENT,"
                 "first_name TEXT NOT NULL,"
                 "last_name TEXT NOT NULL,"
                 "username TEXT NOT NULL,"
                 "password TEXT NOT NULL)")
    print("user table created successfully")
    conn.close()


# TABLE CREATED FOR THE PRODUCTS(TABLE 2)
def init_product_table():
    with sqlite3.connect('sale.db') as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS product (id INTEGER PRIMARY KEY AUTOINCREMENT,"
                     "item TEXT NOT NULL,"
                     "price TEXT NOT NULL,"
                     "date_listed TEXT NOT NULL)")
    print("product table created successfully.")


init_user_table()
init_product_table()
users = fetch_users()

# WHAT DOES THIS MEAN ?
username_table = { u.username: u for u in users }
userid_table = { u.id: u for u in users }


def authenticate(username, password):
    user = username_table.get(username, None)
    if user and hmac.compare_digest(user.password.encode('utf-8'), password.encode('utf-8')):
        return user


def identity(payload):
    user_id = payload['identity']
    return userid_table.get(user_id, None)


app = Flask(__name__)
app.debug = True
app.config['SECRET_KEY'] = 'super-secret'
CORS(app)

jwt = JWT(app, authenticate, identity)


@app.route('/protected')
@jwt_required()
def protected():
    return '%s' % current_identity


@app.route('/user-registration/', methods=["POST"])
def user_registration():
    response = {}

    if request.method == "POST":

        first_name = request.form['first_name']
        last_name = request.form['last_name']
        username = request.form['username']
        password = request.form['password']

        with sqlite3.connect("sale.db") as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO user("
                           "first_name,"
                           "last_name,"
                           "username,"
                           "password) VALUES(?, ?, ?, ?)", (first_name, last_name, username, password))
            conn.commit()
            response["message"] = "success"
            response["status_code"] = 201
        return response


@app.route('/add-item/', methods=["POST"])
@jwt_required()
def add_product():
    response = {}

    if request.method == "POST":
        item = request.form['item']
        price = request.form['price']
        date_listed = datetime.datetime.now()

        with sqlite3.connect('sale.db') as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO product("
                           "item,"
                           "price,"
                           "date_listed) VALUES(?, ?, ?)", (item, price, date_listed))
            conn.commit()
            response["status_code"] = 201
            response['description'] = "item was added successfully"
        return response


@app.route('/view-cart/', methods=["GET"])
def get_blogs():
    response = {}
    with sqlite3.connect("sale.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM product")

        posts = cursor.fetchall()

    response['status_code'] = 200
    response['data'] = posts
    return response


@app.route('/get-users/', methods=["GET"])
def get_user():
    response = {}
    with sqlite3.connect("sale.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM user")

        posts = cursor.fetchall()

    response['status_code'] = 200
    response['data'] = posts
    return response


@app.route("/delete-product/<int:product_id>")
@jwt_required()
def delete_product(product_id):
    response = {}
    with sqlite3.connect("sale.db") as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM product WHERE id=" + str(product_id))
        conn.commit()
        response['status_code'] = 200
        response['message'] = "product deleted successfully."
    return jsonify(response)


@app.route('/edit-item/<int:product_id>/', methods=["PUT"])
@jwt_required()
def edit_product(product_id):
    response = {}

    if request.method == "PUT":
        with sqlite3.connect('sale.db') as conn:
            incoming_data = dict(request.json)
            put_data = {}

            if incoming_data.get("item") is not None:
                put_data["item"] = incoming_data.get("item")
                with sqlite3.connect('sale.db') as conn:
                    cursor = conn.cursor()
                    cursor.execute("UPDATE post SET item =? WHERE id=?", (put_data["item"], product_id))
                    conn.commit()
                    response['message'] = "Update was successfully"
                    response['status_code'] = 200
            if incoming_data.get("price") is not None:
                put_data['price'] = incoming_data.get('price')

                with sqlite3.connect('sale.db') as conn:
                    cursor = conn.cursor()
                    cursor.execute("UPDATE product SET price =? WHERE id=?", (put_data["price"], product_id))
                    conn.commit()

                    response["price"] = "Product updated successfully"
                    response["status_code"] = 200
    return response


@app.route('/get-product/<int:product_id>/', methods=["GET"])
def get_post(post_id):
    response = {}

    with sqlite3.connect("sale.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM product WHERE id=" + str(post_id))

        response["status_code"] = 200
        response["description"] = "Product retrieved successfully"
        response["data"] = cursor.fetchone()

    return jsonify(response)