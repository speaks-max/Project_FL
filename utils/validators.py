def is_valid_name(name):
    name = name.strip()
    if len(name) < 3:
        return False
    for ch in name:
        if not (ch.isalpha() or ch == " "):
            return False
    return True

def is_valid_mobile(mobile):
    if len(mobile) != 10:
        return False
    if mobile[0] not in "6789":
        return False
    if not mobile.isdigit():
        return False
    return True

def is_strong_password(password):
    if len(password) < 8:
        return False

    has_upper = has_lower = has_digit = has_special = False

    for ch in password:
        if ch.isupper():
            has_upper = True
        elif ch.islower():
            has_lower = True
        elif ch.isdigit():
            has_digit = True
        else:
            has_special = True

    return has_upper and has_lower and has_digit and has_special
