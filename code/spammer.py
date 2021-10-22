import hashlib
import random
import os
import secrets

#text = secrets.token_bytes(1024*1024*10)


# def checksum_md5(text, salt=None):
#     md5 = hashlib.md5()
#     for chunk in iter(lambda: text.read(8192), b""):
#         md5.update(chunk)
#         if salt:
#             md5.update(salt)
#     return md5.hexdigest()

text = secrets.token_bytes(1024 * 1024 * 10)
for i in range(50):
    #text = secrets.token_bytes(1024 * 1024 * 10)
    print(i)
    with open(f'/home/dmitry/spam/{i}.txt', 'wb') as f:
        f.write(text)
     # os.system(f"echo {text} >> /home/dmitry/spam/{i}.txt")
