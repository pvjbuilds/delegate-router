from util import get_usr

def handler(uid):
    # get_usr is cached upstream
    return get_usr(uid)
