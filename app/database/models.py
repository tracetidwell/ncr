import hashlib
from typing import List

from sqlalchemy.engine.result import ResultProxy

from app.database import db


class Inventory_T(db.Model):

	__table__ = db.Model.metadata.tables['Inventory_T']

	def add_items(filename: str, tags: List[str]) -> None:

		for tag in tags:

			db.session.add(Inventory_T(ImagePath=filename, Tag=tag))

		db.session.commit()


	def get_all_items() -> ResultProxy:

		return db.session.execute(db.session.query(Inventory_T.ImagePath).distinct())


	def get_items_by_tag(tag) -> ResultProxy:

		#return Inventory_T.query.filter_by(Tag=tag).all()
		return db.session.query(Inventory_T.ImagePath).filter_by(Tag=tag).all()


class Users_T(db.Model):

	__table__ = db.Model.metadata.tables['Users_T']

	def add_user(username: str, password: str, firstname: str, lastname: str) -> None:

		db.session.add(Users_T(UserName=username,
							   PasswordHash=password,
							   FirstName=firstname,
							   LastName=lastname))

		db.session.commit()


	def verify_user(username, password):

		if Users_T.user_exists(username):

			if hashlib.md5(password.encode('utf8')).hexdigest() == Users_T.get_password_hash(username):
				return True, ''

			else:
				return False, 'Password does not match'

		else:
			return False, 'Username does not exist'


	def user_exists(username):

		return Users_T.query.filter_by(UserName=username).first() is not None


	def get_password_hash(username):

		return Users_T.query.filter_by(UserName=username).first().PasswordHash


	def get_all_items() -> ResultProxy:

		return db.session.execute(db.session.query(Inventory_T.ImagePath).distinct())


	def get_items_by_tag(tag) -> ResultProxy:

		#return Inventory_T.query.filter_by(Tag=tag).all()
		return db.session.query(Inventory_T.ImagePath).filter_by(Tag=tag).all()

	# def __repr__(self):
	# 	return self.OrderID
    #
	# def add_Order(order):
	# 	if Order_T.query.filter_by(OrderID=order['OrderID']).first() is None:
	# 		new_Order = Order_T(OrderID=order.get('OrderID'),
	# 							MerchantID=order.get('MerchantID'),
	# 							CustomerID=order.get('CustomerID'),
	# 							Quantity=order.get('Quantity'),
	# 							PickupID=order.get('PickupID'),
	# 							DestinationID=order.get('DestinationID'),
	# 							TrackerID=order.get('TrackerID'),
	# 							Status=order.get('Status'),
	# 							Payment=order.get('Payment'),
	# 							Penalty=order.get('Penalty'))
	# 		db.session.add(new_Order)
	# 		db.session.commit()
	# 		return True
	# 	else:
	# 		return False
