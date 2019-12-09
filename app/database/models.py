# Import standard libraries
import hashlib
from typing import List, Tuple

# Import SQLAlchemy
from sqlalchemy.engine.result import ResultProxy

# Import database object
from app.database import db


class Inventory_T(db.Model):
	"""For interacting with Inventory_T database table
	"""

	# Retrieve table metadata
	__table__ = db.Model.metadata.tables['inventory_t']

	def add_item(filename: str, tags: List[str]) -> None:
		"""Add image path and associated tags to database

		Parameters
		----------
		filename : str
				   Filepath to where image is stored on disk
		tags : [str]
			   List of tags to be associated with given image

		Returns
		-------
		None
		"""

		for tag in tags:

			db.session.add(Inventory_T(ImagePath=filename, Tag=tag))

		db.session.commit()


	def get_all_items() -> ResultProxy:
		"""Gets all unique image paths

		Parameters
		----------
		None

		Returns
		-------
		results: ResultProxy
				 Iteratable of lists, where each list is a row returned from the database
		"""

		return db.session.execute(db.session.query(Inventory_T.ImagePath).distinct())


	def get_items_by_tag(tag: str) -> ResultProxy:
		"""Gets all unique image paths

		Parameters
		----------
		tag: str
			 Tag by which to filter the image paths

		Returns
		-------
		results: ResultProxy
				 Iteratable of lists, where each list is a row returned from the database
		"""

		return db.session.query(Inventory_T.ImagePath).filter_by(Tag=tag).all()


class Users_T(db.Model):
	"""For interacting with Users_T database table
	"""

	# Retrieve table metadata
	__table__ = db.Model.metadata.tables['users_t']

	def add_user(username: str, password: str, firstname: str, lastname: str) -> None:

		db.session.add(Users_T(UserName=username,
							   PasswordHash=hashlib.md5(password.encode('utf8')).hexdigest(),
							   FirstName=firstname,
							   LastName=lastname))

		db.session.commit()


	def verify_user(username: str, password: str) -> Tuple[bool, str]:

		# Check to see if user exists
		if Users_T.user_exists(username):

			# If hashed password matches stored hash for that user, verification is successful and notifies user
			if hashlib.md5(password.encode('utf8')).hexdigest() == Users_T.get_password_hash(username):
				return True, ''

			# If password doesn't match, verification fails and notfies user
			else:
				return False, 'Password does not match'

		# If user does not exist, verification fails and notifies user
		else:
			return False, 'Username does not exist'


	def user_exists(username: str) -> bool:
		"""Checks to see if user exists in database

		Parameters
		----------
		username : str
				   Username as a string

		Returns
		-------
		exists : bool
				 Boolean indicating whether username exists in Users_T database
		"""

		return Users_T.query.filter_by(UserName=username).first() is not None


	def get_password_hash(username: str) -> str:
		"""Gets hashed password for given user

		Parameters
		----------
		username : str
				   Username as a string

		Returns
		-------
		hashed_password : str
				 		  String representation of hashed password
		"""

		return Users_T.query.filter_by(UserName=username).first().PasswordHash
