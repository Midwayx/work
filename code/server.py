import hashlib
import socketserver, time
import pickle
import sys
import threading
import secrets
myHost = ''
myPort = 50007
sent = []
INFO = ['WARNING-CHANGES']

clients = {}


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
    while True:
        cmd_list = clients
        row_reply = ('cmd',) + tuple(x for x in input().strip().split())
        reply = pickle.dumps(row_reply)
        conn.send(reply)
        sent.append(row_reply)


def main_thread():
    while True:
        client, *cmd = tuple(x for x in input().strip().split())
        if client in clients:
            print('[MAIN THREAD]: cmd added')
            clients[client].append(('cmd', )+tuple(cmd))
        elif client.lower() == 'exit':
            break
        else:
            print(f'This client {client} not found')
        print(clients)
        print('[MAIN THREAD]: list of sent command ', sent)


class MyClienthandler(socketserver.BaseRequestHandler):

    def __init__(self, request, client_address, server):
        self.client_ip, self.client_port = client_address
        self.salt = secrets.token_bytes(16)
        self.check_sum = 0
        super().__init__(request, client_address, server)

    def auth(self):
        self.request.settimeout(60)
        clients[self.client_ip] = []
        salt_msg = pickle.dumps(('salt', self.salt))  # TODO добавить в словарь с именами потоков
        self.check_sum = checksum_md5('/home/user/Projects/checker/code/wtchdog.py', salt=self.salt)
        if self.client_ip == '192.168.192.130':
            check_sum = checksum_md5('/home/midway/NIRS/code/work/code/files/1.py', salt=self.salt)

        print(f'[CONNECTION REQUEST {self.client_ip}:{self.client_port}] at {now()}')
        print(f'[AUTH DATA] SALT = {self.salt} CHECK_SUM = {self.check_sum}')
        while True:
            data = pickle.loads(self.request.recv(1024))
            # print(data)
            if data[0] == 'ready to auth':
                self.request.send(salt_msg)
            elif data[0] == self.salt:
                if data[1] == self.check_sum:
                    break
                else:
                    output_1 = f'Client send {data[1]}'
                    output_2 = f'Server stored {self.check_sum}'
                    max_len = max(len(output_1), len(output_2))
                    print(f'[{self.client_address}] {"Auth failed!".upper()}\n'
                          f'[{self.client_address}] {output_1:>{max_len}}\n'
                          f'[{self.client_address}] {output_2:>{max_len}}', file=sys.stderr)
                    print('Connection close')
                    return 'AUTH FAILED'
        print(f'[{self.client_address} {threading.currentThread()}] Successful authorization. Key = {self.salt}')
        return 'SUCCESS AUTH'

    def handle(self) -> None:

        try:
            auth = self.auth()
        except TimeoutError:
            auth = 'AUTH FAILED'

        if auth == 'AUTH FAILED':
            self.request.close()
        elif auth == 'SUCCESS AUTH':
            try:
                th = threading.Thread(target=self.send_com, name=self.client_ip+'_sender')
                th.daemon = True
                th.start()
                while True:
                    data = self.request.recv(1024)  # TODO Похоже, что блокирует цикл
                    if not data:
                        break
                    ans = pickle.loads(data)
                    if ans[0] == 'KEEP-ALIVE':
                        if ans[2] == self.check_sum and ans[3] == self.salt:
                            reply = pickle.dumps(('info', 'OK KEEP-ALIVE', now()))
                            self.request.send(reply)
                        else:
                            reply = pickle.dumps(('CRITICAL ERROR', now(), self.check_sum, self.salt))
                            self.request.send(reply)
                            print(f'[CRITICAL] Received hashsum from {self.client_address} isn`t correct:\n'
                                  f'Server stored {self.check_sum}\nClient sent {ans[2]}', file=sys.stderr)
                    elif ans[0] in INFO:  # TODO if 'ok', .., if not ok
                        print(ans)
                    elif ans[0] in sent:
                        if ans[1] == 'OK':
                            print(f'[{self.client_ip} RESPONSE]: ', ans)
                            sent.remove(ans[0])  # TODO Валидация очереди
                        else:
                            print(f'[{self.client_ip} RESPONSE]: ', ans)
            finally:
                self.request.close()
                print('close connection')
                print(f'[CRITICAL] lost connection with {self.client_address}', file=sys.stderr)

    def send_com(self):
        conn = self.request
        while True:
            cmd_list = clients[self.client_address[0]]
            #print(cmd_list, threading.currentThread().name)
            for i in cmd_list:
                reply = pickle.dumps(i)
                conn.send(reply)
                sent.append(i)
                cmd_list.remove(i)
            time.sleep(2)


myaddr = (myHost, myPort)
server = socketserver.ThreadingTCPServer(myaddr, MyClienthandler)
server_thread = threading.Thread(target=server.serve_forever)
server_thread.name = 'server_thread'
server_thread.daemon = True
server_thread.start()
print("Server loop running in thread:", server_thread.name)
try:
    main_thread()
finally:
    server.server_close()
    print('close server')


