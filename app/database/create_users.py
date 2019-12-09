# Import standard libraries
import json
import argparse
import hashlib

# Import SQLAlchemy
import sqlalchemy as sa
from sqlalchemy.orm import Session
from sqlalchemy import MetaData
from sqlalchemy.ext.automap import automap_base as AutomapBase


def create_users(db_creds_path: str, new_users_path: str) -> None:
    """Add new users to users_t database table

    Parameters
    ----------
    db_creds_path : str
                    Relative path from root folder to database credentials json
    new_users_path : str
                     Relative path from root folder to new users text file

    Returns
    -------
    None
    """

    # Read the database credentials from the json file
    with open(db_creds_path) as json_file:
        db_creds = json.load(json_file)

    # Read the new users data from the txt file
    with open(new_users_path, 'r') as f:
        users_info = f.readlines()

    # Create the connection to the database
    engine = sa.create_engine(f"mysql+pymysql://{db_creds['username']}:{db_creds['password']}@localhost/ncr")
    session = Session(engine)

    # Retrieve metadata from database, which allows use of existing tables
    metadata = MetaData()
    metadata.reflect(engine)

    # Produce a set of mappings from the metadata
    base = AutomapBase(metadata=metadata)
    base.prepare()

    # Initialize Users_T for adding new users
    Users_T = base.classes.users_t

    # Iterate through each user in the text file
    for user_info in users_info:

        # Create a new user and add to the database
        username, password, firstname, lastname = user_info.strip().split(',')
        new_user = Users_T(UserName=username,
                           PasswordHash=hashlib.md5(password.encode('utf8')).hexdigest(),
                           FirstName=firstname,
                           LastName=lastname)

        session.add(new_user)
    session.commit()


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--db_creds_path', type=str, default='app/creds/db_creds.json', help='Path to database credentials')
    parser.add_argument('--new_users_path', type=str, default='app/database/users.txt', help='Path to new users file')
    args = parser.parse_args()

    create_users(args.db_creds_path, args.new_users_path)
