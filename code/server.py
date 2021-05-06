import hashlib
import socketserver, time
import pickle
import threading
import secrets
myHost = ''
myPort = 50007
sent = []
#last_update = time.time()
INFO = ['WARNING-CHANGES']


def now():
    return time.ctime(time.time())


def checksum_md5(filename, salt=None):
    md5 = hashlib.md5()
    with open(filename, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            md5.update(chunk)
            if salt:
                md5.update(salt)
    return md5.hexdigest()


def send_com(conn):
    #reply = pickle.dumps(['add', '/home/midway/test/th'])
    while True:
        row_reply = tuple(x for x in input().strip().split())
        reply = pickle.dumps(row_reply)
        conn.send(reply)
        sent.append(row_reply)

        # data = conn.recv(1024)
        # if not data:
        #     time.sleep(1)
        #     continue
        # print(pickle.loads(data))
        # time.sleep(36)


class MyClienthandler(socketserver.BaseRequestHandler):
    def handle(self) -> None:
        last_update = time.time()
        salt = pickle.dumps(('salt', secrets.token_bytes(16)))  # TODO добавить в словарь с именами потоков
        check_sum = checksum_md5('/home/user/Projects/checker/code/wtchdog.py', salt=pickle.loads(salt)[1])

        print(self.client_address, now())
        #time.sleep(5)
        #salt = pickle.dumps(random.getrandbits(10))
        print(f'salt = {pickle.loads(salt)}, check_sum = {check_sum}')
        self.request.send(salt)
        x = threading.Thread(target=send_com, args=(self.request, ))
        x.start()
        while True:
            print(- last_update + time.time())
            if -last_update + time.time() > 40:
                print(f'[CRITICAL] Connection with {self.client_address} lost!\n'*3)
            data = self.request.recv(1024)  # TODO Похоже, что блокирует цикл
            if not data:
                time.sleep(1)
                continue
            ans = pickle.loads(data)
            #print(sent)
            if ans[0] == 'KEEP-ALIVE':
                if ans[2] == check_sum and ans[3] == pickle.loads(salt)[1]:
                    last_update = time.time()
                    reply = pickle.dumps(('OK KEEP-ALIVE', now()))
                    #print(ans)
                    self.request.send(reply)
                else:
                    reply = pickle.dumps(('CRITICAL ERROR', now(), check_sum, pickle.loads(salt)))
                    self.request.send(reply)
                    self.request.send(data)
            elif ans[0] in INFO:  # TODO if 'ok', .., if not ok
                print(ans)
            elif ans[1] in sent:
                print(ans)
                sent.remove(ans[1])  #TODO Валидация очереди
            #reply = pickle.dumps(['add', '/home/midway/config.txt'])
            #self.request.send(reply)
        self.request.close()
        print('close connection')


myaddr = (myHost, myPort)
server = socketserver.ThreadingTCPServer(myaddr, MyClienthandler)
server.serve_forever()
