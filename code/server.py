import hashlib
import socket
import socketserver, time
import pickle
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
    #reply = pickle.dumps(['add', '/home/midway/test/th'])
    while True:
        cmd_list = clients
        row_reply = ('cmd',) + tuple(x for x in input().strip().split())
        reply = pickle.dumps(row_reply)
        conn.send(reply)
        sent.append(row_reply)


def main_thread():
    while True:
        #print('Жду команд')
        client, *cmd = tuple(x for x in input().strip().split())
        if client in clients:
            print('[MAIN THREAD]: cmd added')
            clients[client].append(('cmd', )+tuple(cmd))
        else:
            print(f'This client {client} not found')
        print(clients)
        print('[MAIN THREAD]: list of sent command ', sent)


class MyClienthandler(socketserver.BaseRequestHandler):
    def handle(self) -> None:
        #threading.currentThread().daemon = True
        self.request.settimeout(60)
        client_ip, client_port = self.client_address
        clients[client_ip] = []
        salt = secrets.token_bytes(16)
        salt_msg = pickle.dumps(('salt', salt))  # TODO добавить в словарь с именами потоков
        check_sum = checksum_md5('/home/midway/NIRS/code/work/code/wtchdog.py', salt=salt)
        if client_ip == '192.168.192.130':
            check_sum = checksum_md5('/home/midway/NIRS/code/work/code/files/1.py', salt=salt)

        print(self.client_address, now())
        print(f'salt = {salt}, check_sum = {check_sum}')
        while True:
            data = pickle.loads(self.request.recv(1024))
            print(data)
            if data[0] == 'ready to auth':
                self.request.send(salt_msg)
            elif data == salt:
                break
        print(f'[{self.client_address} {threading.currentThread()}] Successful authorization. Key = {salt}')
        x = threading.Thread(target=self.send_com, name=client_ip+'_sender')
        x.start()
        while True:
            data = self.request.recv(1024)  # TODO Похоже, что блокирует цикл
            if not data:
                break
                #time.sleep(1)
                #continue
            ans = pickle.loads(data)
            if ans[0] == 'KEEP-ALIVE':
                if ans[2] == check_sum and ans[3] == salt:
                    reply = pickle.dumps(('info', 'OK KEEP-ALIVE', now()))
                    self.request.send(reply)
                else:
                    reply = pickle.dumps(('CRITICAL ERROR', now(), check_sum, salt))
                    self.request.send(reply)
                    print(f'[CRITICAL] received hashsum from {self.client_address} isn`t correct: '
                          f'server stored {check_sum}, but client sent {ans[2]}')
            elif ans[0] in INFO:  # TODO if 'ok', .., if not ok
                print(ans)
            elif ans[0] in sent:
                if ans[1] == 'OK':
                    print(f'[{client_ip} RESPONSE]: ', ans)
                    sent.remove(ans[0])  # TODO Валидация очереди
                else:
                    print(f'[{client_ip} RESPONSE]: ', ans)
        print(f'[CRITICAL] lost connection with {self.client_address}')
        self.request.close()
        print('close connection')

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
server_thread.start()
print("Server loop running in thread:", server_thread.name)
main_thread()
#thread.daemon = True
#server.serve_forever()


