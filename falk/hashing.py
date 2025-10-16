import hashlib


def get_md5_hash(mutable_app, string):
    md5_hash = hashlib.md5()

    md5_hash.update(string.encode())

    return md5_hash.hexdigest()
