import hashlib

class HashLib():
    @classmethod
    def md5(cls,string):
        m = hashlib.md5()
        m.update(string.encode('utf-8'))
        return m.hexdigest()