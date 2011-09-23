# import operator
# import sys

KEY = 'k0'


def xor(string):
    data = ''
    for char in string:
        for ch in KEY:
            char = chr(ord(char) ^ ord(ch))
        data += char
    return data


def encrypt(pk):
    string = str(pk)
    return xor(string)


def decrypt(string):
    string = xor(string)
    pk = int(string)
    return pk
