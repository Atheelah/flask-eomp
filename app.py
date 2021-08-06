# IMPORTING THE MODULES THAT ARE REQUIRED FOR THIS TASK
import hmac
import sqlite3
import datetime
from flask import Flask, request, jsonify
from flask_jwt import JWT, jwt_required, current_identity
from flask_cors import CORS
from flask_mail import Mail, Message



class User(object):
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password

# SALE DATABASE IS BEING CREATED HERE. CREATING A TABLE CALLED USER. WHERE A USER CAN REGISTER THEMSELVES
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
# THE APPROPRIATE FIELDS ARE ADDED HERE IN THE TABLE
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
        # THE APPROPRIATE FIELDS ARE ADDED HERE IN THE TABLE
        conn.execute("CREATE TABLE IF NOT EXISTS product (id INTEGER PRIMARY KEY AUTOINCREMENT,"
                     "item TEXT NOT NULL,"
                     "price TEXT NOT NULL,"
                     "date_listed TEXT NOT NULL)")
    print("product table created successfully.")


init_user_table()   # CALLING THE FUNCTION FOR THE USER TABLE
init_product_table()   # CALLING THE FUNCTION FOR THE PRODUCT TABLE
users = fetch_users()   # CALLING  THE FUNCTION TO FETCH THE USERS

# THIS DISPLAYS THE USERS AND THE ID OF THE USERNAME
username_table = {u.username: u for u in users}
userid_table = {u.id: u for
                u in users}


# CREATING A FUNCTION TO CHECK THE USERNAME AND PASSWORD. TO CHECK IF IT CORRESPONDS
def authenticate(username, password):
    user = username_table.get(username, None)
    if user and hmac.compare_digest(user.password.encode('utf-8'), password.encode('utf-8')):
        return user


# THIS CHECKS THE IDENTITY FI THE ABOVE
def identity(payload):
    user_id = payload['identity']
    return userid_table.get(user_id, None)


# HERE AND EMAIL IS BEING CREATED (EMAIL SYNTAX)
app = Flask(__name__)
app.config['MAIL_SERVER'] = 'smtp.gmail.com'   # THIS IS THE SERVER
app.config['MAIL_PORT'] = 465   # THIS IS  THE PORT
app.config['MAIL_USERNAME'] = 'atheelahlifechoices@gmail.com'   # THE USERNAME NEEDS TO BE INSERTED HERE (THE SENDERS)
app.config['MAIL_PASSWORD'] = 'lifechoices1234'   # PASSWORD INSERTED HERE  (THE SENDERS DETAILS)
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail(app)


jwt = JWT(app, authenticate, identity)


# THIS PROTECTS THE SIGHT AND CHECKS THE IDENTITY
@app.route('/protected')
@jwt_required()
def protected():
    return '%s' % current_identity


# THIS IS MY FUNCTION  TO REGISTER A USER.
@app.route('/user-registration/', methods=["POST"])
def user_registration():
    response = {}

    if request.method == "POST":

        first_name = request.form['first_name']
        last_name = request.form['last_name']
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']

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

# MY EMAIL IS ADDED IN HERE
            if response['status_code'] == 201:
                msg = Message('success', sender='atheelahlifechoices@gmail.com', recipients=[email])
                msg.body = 'Your registration was successful.'
                mail.send(msg)
            return "Message sent"


# THIS IS MY FUNCTION TO ADD AN ITEM
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


# THIS IS MY FUNCTION TO VIEW MY CART
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


# THIS IS MY FUNCTION TO GET THE USERS
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


# THIS IS MY FUNCTION TO DELETE AN ITEM
@app.route("/delete-item/<int:product_id>/")
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


# THIS IS MY FUNCTION TO ADD AN ITEM
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


# THIS IS MY FUNCTION TO GET A PRODUCT
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


# THIS RUNS THE APPLICATION
if __name__ == '__main__':
    app.debug = True
    app.run()
