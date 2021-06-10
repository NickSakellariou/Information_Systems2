from pymongo import MongoClient
from flask import Flask, request, Response, render_template
import json
import uuid
import time
from bson.objectid import ObjectId
import os

# Connect to our local MongoDB
mongodb_hostname = os.environ.get("MONGO_HOSTNAME", "localhost")
client = MongoClient('mongodb://'+mongodb_hostname+':27017/')

# Choose database
db = client['DSMarkets']

# Choose collections
users = db['Users']
products = db['Products']

# Initiate Flask App
app = Flask(__name__)

users_sessions = {}
admin_sessions = {}

cart_products=[]

def user_create_session(email):
    user_uuid = str(uuid.uuid1())
    users_sessions[user_uuid] = (email, time.time())
    return user_uuid  

def user_is_session_valid(user_uuid):
    return user_uuid in users_sessions

def admin_create_session(email):
    user_uuid = str(uuid.uuid1())
    admin_sessions[user_uuid] = (email, time.time())
    return user_uuid  

def admin_is_session_valid(user_uuid):
    return user_uuid in admin_sessions

@app.route('/', methods=['GET'])
def main_page():
    return render_template('main.html')    

@app.route('/register', methods=['POST','GET'])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        if not name or not email or not password:
            return Response("Information incomplete", status=500, mimetype="application/json")


        user1 = users.find_one({"e-mail":email})
        if user1 == None:
            user = {"name": name, "e-mail": email,"password": password, "category": "Simple user","orderHistory": []}
            users.insert_one(user)
            return Response("User was added to the MongoDB",status=200,mimetype='application/json') 
        else:
            return Response("A user with the given e-mail already exists",status=400,mimetype='application/json')

    return render_template("register.html")

@app.route("/login", methods=['POST', 'GET'])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        if not email or not password:
            return Response("Information incomplete", status=500, mimetype="application/json")

        user = users.find_one({"$and": [{"e-mail":email}, {"password":password}]})
        if user !=None:
            if user["category"] == "Simple user":
                user_uuid = user_create_session(email)
                res = {"uuid": user_uuid, "email": email}
                return Response(json.dumps(res),status=200, mimetype='application/json')
            elif user["category"] == "admin":
                user_uuid = admin_create_session(email)
                res = {"uuid": user_uuid, "email": email}
                return Response(json.dumps(res),status=200, mimetype='application/json')

        else:
            return Response("Wrong username or password, please try again.",status=400,mimetype='application/json') 

    return render_template("login.html")     

@app.route("/<string:uuid>/insertProduct", methods=['POST', 'GET'])
def insert_product(uuid):
    if uuid == None:
        return Response("Bad request", status=500, mimetype='application/json')

    if user_is_session_valid(uuid) :
        return Response("Only admins can perform this operation", status=500, mimetype="application/json")
    elif admin_is_session_valid(uuid) :
        if request.method == "POST":
            name = request.form["name"]
            price = request.form["price"]
            description = request.form["description"]
            category = request.form["category"]
            stock = request.form["stock"]

            if not name or not price or not description or not category or not stock:
                return Response("Information incomplete", status=500, mimetype="application/json")

            product = {"name": name,"price": float(request.form["price"]),"description": description,"category": category,"stock": int(request.form["stock"])}

            products.insert_one(product)

            return Response("Product was added to the MongoDB", status=200, mimetype='application/json')

        return render_template("add_product.html") 
    else:
        return Response("Wrong uuid.",status=401,mimetype='application/json')

@app.route("/<string:uuid>/removeProduct/<string:id>", methods=['DELETE', 'GET'])
def remove_product(uuid,id):
    if uuid == None or id == None:
        return Response("Bad request", status=500, mimetype='application/json')

    if user_is_session_valid(uuid) :
        return Response("Only admins can perform this operation", status=500, mimetype="application/json")
    elif admin_is_session_valid(uuid) :
        if not id:
            return Response("Information incomplete", status=500, mimetype="application/json")

        if len(id)!=24:
            return Response('Not valid id, it must be a 24-character hex string ',status=500,mimetype='application/json')
        else:    
            product = products.find_one({"_id": ObjectId(id)})
            if product !=None:
                msg = product['name'] + " was deleted."
                products.delete_one({'_id': ObjectId(id)})
                return Response(msg, status=200, mimetype='application/json')
            else:
                msg = "No product found with that id."
                return Response(msg,status=500,mimetype='application/json')
    else:
        return Response("Wrong uuid.",status=401,mimetype='application/json')

@app.route("/<string:uuid>/updateProduct/<string:id>", methods=['POST', 'GET'])
def update_product(uuid,id):
    if uuid == None or id == None:
        return Response("Bad request", status=500, mimetype='application/json')

    if user_is_session_valid(uuid) :
        return Response("Only admins can perform this operation", status=500, mimetype="application/json")
    elif admin_is_session_valid(uuid) :
        if not id:
            return Response("Information incomplete", status=500, mimetype="application/json")

        if len(id)!=24:
            return Response('Not valid id, it must be a 24-character hex string ',status=500,mimetype='application/json')
        else:

            if request.method == "POST":
                product = products.find_one({"_id": ObjectId(id)})
                if product !=None:
                    name = request.form["name"]
                    price = request.form["price"]
                    description = request.form["description"]
                    stock = request.form["stock"]

                    if not name and not price and not description and not stock:
                        return Response("Information incomplete", status=500, mimetype="application/json")
                        
                    if name:
                        products.update_one(
                            {"_id": ObjectId(id)},
                            {"$set":
                                {
                                    "name": name
                                }
                            }
                        )

                    if price:
                        products.update_one(
                            {"_id": ObjectId(id)},
                            {"$set":
                                {
                                    "price": float(request.form["price"])
                                }
                            }
                        )

                    if description:
                        products.update_one(
                            {"_id": ObjectId(id)},
                            {"$set":
                                {
                                    "description": description
                                }
                            }
                        )

                    if stock:
                        products.update_one(
                            {"_id": ObjectId(id)},
                            {"$set":
                                {
                                    "stock": int(request.form["stock"])
                                }
                            }
                        )

                    return Response("Product was updated to the MongoDB", status=200, mimetype='application/json')
                else:
                    msg = "No product found with that id."
                    return Response(msg,status=500,mimetype='application/json')

            return render_template("update_product.html") 
    else:
        return Response("Wrong uuid.",status=401,mimetype='application/json')

@app.route("/<string:uuid>/searchProducts", methods=['POST', 'GET'])
def search_products(uuid):
    if uuid == None:
        return Response("Bad request", status=500, mimetype='application/json')

    if admin_is_session_valid(uuid) :
        return Response("Only simple users can perform this operation", status=500, mimetype="application/json")
    elif user_is_session_valid(uuid) :
        if request.method == "POST":
            name = request.form["name"]
            category = request.form["category"]
            id = request.form["id"]
            i=0
            if name:
                i+=1
            if category:
                i+=1
            if id:
                i+=1
            if i>1:
                return Response("Only one field at the time", status=500, mimetype="application/json")
            elif i==0:
                return Response("Information incomplete", status=500, mimetype="application/json")
            else:
                if name:
                    iterable = products.find({})

                    output = []

                    for product in iterable:
                        if name in product['name']:
                            product['_id'] = str(product['_id'])
                            product['price'] = str(product['price']) + " €"
                            del product['stock']
                            output.append(product)

                    if output != []:
                        return Response(json.dumps(sorted(output, key=lambda s: s['name'].lower()), indent=4, ensure_ascii=False), status=200, mimetype='application/json')
                    return Response('No product found with that name',status=500,mimetype='application/json')
                if category:
                    iterable = products.find({})

                    output = []

                    for product in iterable:
                        if category == product['category']:
                            product['_id'] = str(product['_id'])
                            product['price'] = str(product['price']) + " €"
                            del product['stock']
                            output.append(product)

                    if output != []:
                        return Response(json.dumps(sorted(output, key=lambda s: s['price']), indent=4, ensure_ascii=False), status=200, mimetype='application/json')
                    return Response('No product found in that category',status=500,mimetype='application/json')
                if id:
                    if len(id)!=24:
                        return Response('Not valid id, it must be a 24-character hex string ',status=500,mimetype='application/json')
                    else:
                        product = products.find_one({"_id": ObjectId(id)})
                        if product !=None:
                            product['_id'] = str(product['_id'])
                            product['price'] = str(product['price']) + " €"
                            del product['stock']
                            return Response(json.dumps(product, indent=4, ensure_ascii=False), status=200, mimetype='application/json')
                        else:
                            return Response('No product found with that id',status=500,mimetype='application/json')

        return render_template("search_products.html") 
    else:
        return Response("Wrong uuid.",status=401,mimetype='application/json')

@app.route("/<string:uuid>/addToCart/<string:id>/<int:stock>", methods=['GET'])
def add_to_cart(uuid, id, stock):
    if uuid == None or id == None or stock == None:
        return Response("Bad request", status=500, mimetype='application/json')

    if admin_is_session_valid(uuid) :
        return Response("Only simple users can perform this operation", status=500, mimetype="application/json")
    elif user_is_session_valid(uuid) :
        if len(id)!=24:
            return Response('Not valid id, it must be a 24-character hex string ',status=500,mimetype='application/json')
        else:
            product = products.find_one({"_id": ObjectId(id)})
            if product !=None:
                if product['stock']<stock:
                    return Response('We don not have that much stock', status=200, mimetype='application/json')
                else:   
                    product["quantity"] = product.pop("stock")
                    product['_id'] = str(product['_id'])
                    found_product = False
                    for cart_product in cart_products:
                        if cart_product['_id'] == id:
                            cart_product['quantity']=stock
                            found_product = True

                    if found_product == False:
                        product['quantity']=stock
                        cart_products.append(product)

                    return render_template("cart.html", cart_products=cart_products)
            else:
                return Response('No product found with that id',status=500,mimetype='application/json')
    else:
        return Response("Wrong uuid.",status=401,mimetype='application/json')
      
@app.route("/<string:uuid>/showCart", methods=['GET'])
def show_cart(uuid):
    if uuid == None:
        return Response("Bad request", status=500, mimetype='application/json')

    if admin_is_session_valid(uuid) :
        return Response("Only simple users can perform this operation", status=500, mimetype="application/json")
    elif user_is_session_valid(uuid) :
        return render_template("cart.html", cart_products=cart_products)
    else:
        return Response("Wrong uuid.",status=401,mimetype='application/json')

@app.route("/<string:uuid>/deleteFromCart/<string:id>", methods=['GET'])
def delete_from_cart(uuid, id):
    if uuid == None or id == None:
        return Response("Bad request", status=500, mimetype='application/json')

    if admin_is_session_valid(uuid) :
        return Response("Only simple users can perform this operation", status=500, mimetype="application/json")
    elif user_is_session_valid(uuid) :
        if len(id)!=24:
            return Response('Not valid id, it must be a 24-character hex string ',status=500,mimetype='application/json')
        else:
            found_product = False
            for cart_product in cart_products:
                if cart_product['_id'] == id:
                    cart_products.remove(cart_product)
                    found_product = True

            if found_product == False:
                return Response('No product found with that id in cart',status=500,mimetype='application/json')
            else:
                return render_template("cart.html", cart_products=cart_products)
    else:
        return Response("Wrong uuid.",status=401,mimetype='application/json')

@app.route("/<string:uuid>/buyProducts", methods=['POST', 'GET'])
def buy_products(uuid):
    if uuid == None:
        return Response("Bad request", status=500, mimetype='application/json')

    if admin_is_session_valid(uuid) :
        return Response("Only simple users can perform this operation", status=500, mimetype="application/json")
    elif user_is_session_valid(uuid) :
        if request.method == "POST":
            if len(cart_products) == 0:
                return Response('Cart is empty',status=500,mimetype='application/json')
            else:
                for cart_product in cart_products:
                    product = products.find_one({"_id":ObjectId(cart_product["_id"])})
                    quantity = product["stock"] - cart_product["quantity"]
                    products.update_one({"_id": ObjectId(cart_product["_id"])},{"$set":{"stock": int(quantity)}})
                users.update_one({'e-mail': users_sessions[uuid][0]}, {'$push': {"orderHistory": cart_products }})
                card_number = request.form["card_number"]
                def RepresentsInt(s):
                    try: 
                        int(s)
                        return True
                    except ValueError:
                        return False
                if len(str(card_number)) != 16 or RepresentsInt(card_number) == False: 
                    return Response('Card number must contain 16 numbers',status=500,mimetype='application/json')
                else:
                    bought_products = cart_products.copy()
                    cart_products.clear()
                    return render_template("buy_products.html", bought_products=bought_products, card_number=card_number)
        return render_template("buy_products.html") 
    else:
        return Response("Wrong uuid.",status=401,mimetype='application/json')

@app.route("/<string:uuid>/showOrderHistory", methods=['GET'])
def show_order_history(uuid):
    if uuid == None:
        return Response("Bad request", status=500, mimetype='application/json')

    if admin_is_session_valid(uuid) :
        return Response("Only simple users can perform this operation", status=500, mimetype="application/json")
    elif user_is_session_valid(uuid) :
        order_history=[]
        user = users.find_one({"e-mail":users_sessions[uuid][0]})
        order_history=user["orderHistory"]
        if order_history!=None:
            return render_template("order_history.html", order_history=order_history)
        else:
            return Response("Order history is empty",status=500,mimetype='application/json')
    else:
        return Response("Wrong uuid.",status=401,mimetype='application/json')

@app.route("/<string:uuid>/deleteUser", methods=['DELETE','GET'])
def delete_user(uuid):
    if uuid == None:
        return Response("Bad request", status=500, mimetype='application/json')

    if admin_is_session_valid(uuid) :
        return Response("Only simple users can perform this operation", status=500, mimetype="application/json")
    elif user_is_session_valid(uuid) :
        msg = users_sessions[uuid][0] + " was deleted."
        users.delete_one({'e-mail': str(users_sessions[uuid][0])})
        users_sessions.clear()
        return Response(msg, status=200, mimetype='application/json')
    else:
        return Response("Wrong uuid.",status=401,mimetype='application/json')

# Εκτέλεση flask service σε debug mode, στην port 5000. 
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)