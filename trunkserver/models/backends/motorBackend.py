__author__ = 'colprog'

import motor

db_connection = None


def get_connection():
    return db_connection


def connect(uri):
    global db_connection
    # db_connection = motor.MotorReplicaSetClient(host, replicaSet=replSet, max_pool_size=200)
    db_connection = motor.MotorClient(uri)
    return db_connection


def get_db(db_alias):
    return db_connection[db_alias]


def reset():
    for p in db_connection._get_pools():
        p.reset()
