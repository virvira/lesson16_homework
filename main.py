from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
import prettytable
import json
import os.path

USERS_FILE = os.path.join("data", "users.json")
ORDERS_FILE = os.path.join("data", "orders.json")
OFFERS_FILE = os.path.join("data", "offers.json")

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db: SQLAlchemy = SQLAlchemy(app)


class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String)
    last_name = db.Column(db.String)
    age = db.Column(db.Integer)
    email = db.Column(db.String)
    role = db.Column(db.String)
    phone = db.Column(db.String)

    def return_data(self):
        return {
            "id": self.id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "age": self.age,
            "email": self.email,
            "role": self.role,
            "phone": self.phone
        }


class Offer(db.Model):
    __tablename__ = "offer"
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("order_.id"))
    executor_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    order = db.relationship("Order_")
    executor = db.relationship("User")

    def return_data(self):
        return {
            "id": self.id,
            "order": self.order.return_data(),
            "executor": self.executor.return_data()
        }


class Order_(db.Model):
    __tablename__ = "order_"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    description = db.Column(db.Text(1000))
    start_date = db.Column(db.String)
    end_date = db.Column(db.String)
    address = db.Column(db.String)
    price = db.Column(db.Integer)
    customer_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    executor_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    customer = db.relationship("User", foreign_keys=[customer_id])
    executor = db.relationship("User", foreign_keys=[executor_id])

    def return_data(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "address": self.address,
            "price": self.price,
            "customer_id": self.customer_id,
            "executor_id": self.executor_id
        }


with app.app_context():
    db.create_all()
    session = db.session()

    # заполняем таблицу user из json файла
    with open(USERS_FILE, 'r', encoding='utf-8') as json_file:
        users_list = json.load(json_file)

    for i in range(len(users_list)):
        user = User(id=users_list[i]['id'],
                    first_name=users_list[i]['first_name'],
                    last_name=users_list[i]['last_name'],
                    age=users_list[i]['age'],
                    email=users_list[i]['email'],
                    role=users_list[i]['role'],
                    phone=users_list[i]['phone']
                    )
        session.add(user)

    session.commit()

    # заполняем таблицу order из json файла
    with open(ORDERS_FILE, 'r', encoding='utf-8') as json_file:
        orders_list = json.load(json_file)

    for i in range(len(orders_list)):
        order = Order_(id=orders_list[i]['id'],
                       name=orders_list[i]['name'],
                       description=orders_list[i]['description'],
                       start_date=orders_list[i]['start_date'],
                       end_date=orders_list[i]['end_date'],
                       address=orders_list[i]['address'],
                       price=orders_list[i]['price'],
                       customer_id=orders_list[i]['customer_id'],
                       executor_id=orders_list[i]['executor_id']
                       )
        session.add(order)

    session.commit()

    # заполняем таблицу offer из json файла
    with open(OFFERS_FILE, 'r', encoding='utf-8') as json_file:
        offers_list = json.load(json_file)

    for i in range(len(offers_list)):
        offer = Offer(id=offers_list[i]['id'],
                      order_id=offers_list[i]['order_id'],
                      executor_id=offers_list[i]['executor_id']
                      )
        session.add(offer)

    session.commit()

    cursor_user = session.execute("select * from user").cursor
    user_table = prettytable.from_db_cursor(cursor_user)
    cursor_offer = session.execute("select * from offer").cursor
    offer_table = prettytable.from_db_cursor(cursor_offer)
    cursor_order = session.execute("select * from order_").cursor
    order_table = prettytable.from_db_cursor(cursor_order)


@app.route("/users", methods=['GET'])
def all_users():
    users = db.session.query(User).all()
    res = []
    for user in users:
        res.append(user.return_data())
    return json.dumps(res, indent=4)


@app.route('/users', methods=['POST'])
def create_user():
    data = request.json
    db.session.add(
        User(**data)
    )
    db.session.commit()
    return "OK"


@app.route("/users/<int:user_id>", methods=['GET'])
def user_by_id(user_id):
    user = db.session.query(User).get(user_id)
    if user is None:
        return app.response_class(
            "User not found",
            mimetype='text/plain',
            status=404
        )
    res = user.return_data()
    return json.dumps(res, indent=4)


@app.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    data = request.json
    user = db.session.query(User).get(user_id)

    required_fields = [
        'id',
        'first_name',
        'last_name',
        'age',
        'email',
        'role',
        'phone',
    ]

    for field in required_fields:
        if field not in data:
            return app.response_class(
                f'Поле {field} обязательно',
                mimetype='text/plain',
                status=400
            )

    user.id = data['id']
    user.first_name = data['first_name']
    user.last_name = data['last_name']
    user.age = data['age']
    user.email = data['email']
    user.role = data['role']
    user.phone = data['phone']
    db.session.commit()

    return app.response_class(
        json.dumps("OK"),
        mimetype='application/json',
        status=200
    )


@app.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    user = db.session.query(User).get(user_id)
    if user is None:
        return app.response_class(
            "User not found",
            mimetype='text/plain',
            status=404
        )

    db.session.query(User).filter(User.id == user_id).delete()
    db.session.commit()
    return app.response_class(
        json.dumps("OK"),
        mimetype='application/json',
        status=200
    )


@app.route("/orders", methods=['GET'])
def all_orders():
    orders = db.session.query(Order_).all()
    res = []
    for order in orders:
        res.append(order.return_data())
    return json.dumps(res, indent=4, ensure_ascii=False)


@app.route('/orders', methods=['POST'])
def create_order():
    data = request.json
    db.session.add(
        Order_(**data)
    )
    db.session.commit()
    return "OK"


@app.route("/orders/<int:order_id>", methods=['GET'])
def order_by_id(order_id):
    order = db.session.query(Order_).get(order_id)
    if order is None:
        return app.response_class(
            "Order not found",
            mimetype='text/plain',
            status=404
        )
    res = order.return_data()
    return json.dumps(res, indent=4, ensure_ascii=False)


@app.route('/orders/<int:order_id>', methods=['PUT'])
def update_order(order_id):
    data = request.json
    order = db.session.query(Order_).get(order_id)

    required_fields = [
        'id',
        'name',
        'description',
        'start_date',
        'end_date',
        'address',
        'price',
        'customer_id',
        'executor_id'
    ]

    for field in required_fields:
        if field not in data:
            return app.response_class(
                f'Поле {field} обязательно',
                mimetype='text/plain',
                status=400
            )

    order.id = data['id']
    order.name = data['name']
    order.description = data['description']
    order.start_date = data['start_date']
    order.end_date = data['end_date']
    order.address = data['address']
    order.price = data['price']
    order.customer_id = data['customer_id']
    order.executor_id = data['executor_id']

    db.session.commit()

    return app.response_class(
        json.dumps("OK"),
        mimetype='application/json',
        status=200
    )


@app.route('/orders/<int:order_id>', methods=['DELETE'])
def delete_order(order_id):
    order = db.session.query(Order_).get(order_id)
    if order is None:
        return app.response_class(
            "User not found",
            mimetype='text/plain',
            status=404
        )

    db.session.query(Order_).filter(Order_.id == order_id).delete()
    db.session.commit()
    return app.response_class(
        json.dumps("OK"),
        mimetype='application/json',
        status=200
    )


@app.route("/offers", methods=['GET'])
def all_offers():
    offers = db.session.query(Offer).all()
    res = []
    for offer in offers:
        res.append(offer.return_data())
    return json.dumps(res, indent=4, ensure_ascii=False)


@app.route('/offers', methods=['POST'])
def create_offer():
    data = request.json
    db.session.add(
        Offer(**data)
    )
    db.session.commit()
    return "OK"


@app.route("/offers/<int:offer_id>", methods=['GET'])
def offer_by_id(offer_id):
    offer = db.session.query(Offer).get(offer_id)
    if offer is None:
        return app.response_class(
            "Offer not found",
            mimetype='text/plain',
            status=404
        )
    res = offer.return_data()
    return json.dumps(res, indent=4, ensure_ascii=False)


@app.route('/offers/<int:offer_id>', methods=['PUT'])
def update_offer(offer_id):
    data = request.json
    offer = db.session.query(Offer).get(offer_id)

    required_fields = [
        'id',
        'order_id',
        'executor_id'
    ]

    for field in required_fields:
        if field not in data:
            return app.response_class(
                f'Поле {field} обязательно',
                mimetype='text/plain',
                status=400
            )

    offer.id = data['id']
    offer.order_id = data['order_id']
    offer.executor_id = data['executor_id']

    db.session.commit()

    return app.response_class(
        json.dumps("OK"),
        mimetype='application/json',
        status=200
    )


@app.route('/offers/<int:offer_id>', methods=['DELETE'])
def delete_offer(offer_id):
    offer = db.session.query(Offer).get(offer_id)
    if offer is None:
        return app.response_class(
            "User not found",
            mimetype='text/plain',
            status=404
        )

    db.session.query(Offer).filter(Offer.id == offer_id).delete()
    db.session.commit()
    return app.response_class(
        json.dumps("OK"),
        mimetype='application/json',
        status=200
    )


if __name__ == '__main__':
    app.run('localhost', port=8000, debug=True)
