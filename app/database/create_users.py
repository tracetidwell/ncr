import json
import hashlib

import sqlalchemy as sa
from sqlalchemy.orm import Session
from sqlalchemy import MetaData
from sqlalchemy.ext.automap import automap_base as AutomapBase


with open('app/creds/db_creds.json') as json_file:
    db_creds = json.load(json_file)

engine = sa.create_engine(f"mysql+pymysql://{db_creds['username']}:{db_creds['password']}@localhost/ncr")
session = Session(engine)

metadata = MetaData()
metadata.reflect(engine)

# we can then produce a set of mappings from this MetaData.
base = AutomapBase(metadata=metadata)
base.prepare()

Users_T = base.classes.Users_T

with open('app/database/users.txt', 'r') as f:
    users_info = f.readlines()

for user_info in users_info:
    username, password, firstname, lastname = user_info.strip().split(',')

    new_user = Users_T(UserName=username,
                       PasswordHash=hashlib.md5(password.encode('utf8')).hexdigest(),
                       FirstName=firstname,
                       LastName=lastname)

    session.add(new_user)
session.commit()
