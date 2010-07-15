from db_config import *
import os, sys

def dbshell(dbname, host=MONGODB_HOST, user=MONGODB_USER, password=MONGODB_PASSWORD):
    os.system('mongo %(host)s/%(dbname)s -u %(user)s -p %(password)s' % locals())

if __name__ == '__main__':
    if len(sys.argv) > 1:
        dbshell(sys.argv[1])
    else:
        dbshell('conceptdb')
