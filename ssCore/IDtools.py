
b62_digits = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'


def get_id(id) :
    new_id = id[-22:]
    return new_id

def is_base62(id):
    b62 = True
    for letter in id :
        if letter not in b62_digits:
            b62 = False
            break
    return b62

def is_id(id) :
    return len(id) == 22 and is_base62(id)
