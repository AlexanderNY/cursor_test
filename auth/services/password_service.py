import bcrypt


def hash_password(password: str) -> str:
    """Хеширование пароля с использованием bcrypt."""
    salt = bcrypt.gensalt(rounds=12)
    password_bytes = password.encode('utf-8')
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


def verify_password(password: str, password_hash: str) -> bool:
    """Проверка пароля против хеша."""
    password_bytes = password.encode('utf-8')
    password_hash_bytes = password_hash.encode('utf-8')
    return bcrypt.checkpw(password_bytes, password_hash_bytes)

