from sshtunnel import SSHTunnelForwarder
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from functools import wraps
import sys
sys.path.append(r"C:\Users\silvh\OneDrive\lighthouse\Ginkgo coding\content-summarization\private")

# secrets.py contains credentials, etc.
import db_secrets

def get_engine_for_port(port):
    return create_engine('postgresql://{user}:{password}@{host}:{port}/{db}'.format(
        user=db_secrets.pg_user,
        password=db_secrets.pg_password,
        host='127.0.0.1',
        port=port,
        db=db_secrets.db
    ))

def with_sql_session(function, args, kwargs, engine=None):
    if engine is None:
        # Default to local port
        engine = get_engine_for_port(5432)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        return function(session, *args, **kwargs)
    finally:
        session.close()

def with_local_sql_session(function, *args, **kwargs):
    return with_sql_session(function, args, kwargs)

def with_remote_sql_session(function, *args, **kwargs):
    # Hat tip: https://stackoverflow.com/a/38001815
    with SSHTunnelForwarder(
            (db_secrets.server_ip_address, 5995), # SH 2023-06-25 12:50 changed from 22 to 5995
            ssh_username=db_secrets.ssh_username,
            ssh_pkey=db_secrets.ssh_private_key_path,
            ssh_private_key_password=db_secrets.ssh_private_key_password,
            remote_bind_address=('127.0.0.1', 5432)
        ) as tunnel:
        tunnel.start()
        engine = get_engine_for_port(tunnel.local_bind_port)
        return with_sql_session(function, args, kwargs, engine=engine)

# Decorators
def local_sql_session(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        return with_local_sql_session(function, *args, **kwargs)
    return wrapper

def remote_sql_session(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        return with_remote_sql_session(function, *args, **kwargs)
    return wrapper