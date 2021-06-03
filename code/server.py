import hashlib
import os.path
import socketserver, time
import pickle
import sys
import threading
import secrets
import tkinter as tk
import tkinter.ttk as ttk
from tkinter.messagebox import *

import gui.main
import gui.tree2

myHost = ''
myPort = 50007
sent = []
INFO = ['WARNING-CHANGES']
ALLOWED_HOSTS = {'127.0.0.1': 'ghost1', }
CONNECTED_HOSTS = {}
HOSTS_UNDER_CONTROL = {}

clients = {}
resp = {}


def now():
    return time.ctime(time.time())


def valid_ipv4(ip):
    lst = ip.split('.')
    if len(lst) != 4:
        return False
    for i in lst:
        if int(i) > 255 or int(i) < 0:
            return False
    return True


def checksum_md5(filename, salt=None):
    md5 = hashlib.md5()
    with open(filename, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            md5.update(chunk)
            if salt:
                md5.update(salt)
    return md5.hexdigest()


def checksum_sha(filename, salt=None):
    sha = hashlib.sha256()
    with open(filename, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            sha.update(chunk)
            if salt:
                sha.update(salt)
    return sha.hexdigest()


foo = """
def checksum_sha(filename, salt=None):
    sha = hashlib.sha256()
    with open(filename, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            sha.update(chunk)
            if salt:
                sha.update(salt)
    return sha.hexdigest()
check_sum2 = checksum_sha(sys.argv[0],salt=salt)"""


def send_com(conn):
    while True:
        cmd_list = clients
        row_reply = ('cmd',) + tuple(x for x in input().strip().split())
        reply = pickle.dumps(row_reply)
        conn.send(reply)
        sent.append(row_reply)


def main_thread():
    global b
    a = serverUI()
    # gui.main.foo()
    b = Tree(a.parent, '')
    a.tree = b
    # b.update('ghost3')
    #print(Tree.get_checked)
    tk.mainloop()
    while True:
        client, *cmd = tuple(x for x in input().strip().split())
        if client in clients:
            print('[MAIN THREAD]: cmd added')
            clients[client].append(('cmd',) + tuple(cmd))
        elif client.lower() == 'exit':
            break
        else:
            print(f'This client {client} not found')
        print(clients)
        print('[MAIN THREAD]: list of sent command ', sent)


def _main_thread():
    while True:
        client, *cmd = tuple(x for x in input().strip().split())
        if client in clients:
            print('[MAIN THREAD]: cmd added')
            clients[client].append(('cmd',) + tuple(cmd))
        elif client.lower() == 'exit':
            break
        else:
            print(f'This client {client} not found')
        print(clients)
        print('[MAIN THREAD]: list of sent command ', sent)


class serverUI(gui.main.UI):

    def __init__(self):
        self.tree = None
        super().__init__()

    @staticmethod
    def get_list(flag=None, one=None):
        answer = {}
        q = list()
        timeout = 5
        for client in clients:
            clients[client].append(('cmd', 'get_watchlist', '0'))
            q.append(client)
        while q and timeout:
            for i in q:
                try:
                    ans = resp[i]
                except KeyError:
                    continue
                if ('cmd', 'get_watchlist', '0') in ans:
                    answer[i] = ans[2]
                    q.remove(i)
            time.sleep(0.2)
            timeout -= 0.2
        if flag:
            return answer
        output = [str(i) + ': ' + str(answer[i]) for i in answer]
        showinfo('list', '\n'.join(output))

    def add_file(self):
        pass

    def get_checked(self):
        lst = self.tree.get_checked()
        print(lst)
        showinfo('checked', str(lst))


class Tree(gui.tree2.App):

    def start_up(self, i):
        abspath = '/'
        # for i in clients:
        self.dirs[i] = []
        self.nodes[i] = {}
        self.node[i] = {}
        node = self.tree.insert('', 'end', text=ALLOWED_HOSTS[i], open=False, values=('подключен', 'целостность не нарушена', 'отслеживается'))
        self.parent_nodes[i] = node
        self.tree.tag_add(node, i)
        self.tree.tag_add(node, 'ghost')
        # self.tree.tag_add(node, 'disabled')
        self.nodes[i][node] = abspath
        self.node[i][node] = abspath
        print('Node from startup', node)
        print('Dirs from startup', self.dirs)
        # nt = self.tree.insert('', 'end', text='ghost2', open=False)
        self.insert_node(node, abspath, abspath, i)
        # self.tree.bind('<<TreeviewOpen>>', self.open_node)

    def listdir(self, abspath, client='127.0.0.1'):
        timeout = 5
        clients[client].append(('cmd', 'get_listdir', abspath))
        print('here listdir called')
        while timeout:
            time.sleep(0.2)
            timeout -= 0.2
            try:
                answer = resp[client]  # TODO Решить данный вопрос с наслоением ответов
            except KeyError:
                continue
            if ('cmd', 'get_listdir', abspath) in answer:
                for i in answer[2]:
                    if answer[2][i]:
                        self.dirs[client].append(i)
                return answer[2]

    def update(self, client, path='/'):
        node = self.tree.insert('', 'end', text=client, open=False)
        self.insert_node(node, path, path)

    def send_checked(self):
        #client = '127.0.0.1'  # TODO FIX IT
        checked = self.get_checked()  # TODO add many clients (almost done)
        current_watchdict = serverUI.get_list(flag=True)
        errors = {}
        print(f'[DEBUG] checked={checked}')
        for client in checked:
            for i in checked[client]:
                path = os.path.normpath(i)
                print('path to add', path)
                if i not in current_watchdict[client]:
                    cmd = ('cmd', 'add', path)
                    clients[client].append(cmd)
                else:
                    if client not in errors:
                        errors[client] = [path]
                    else:
                        errors[client].append(path)
        if errors:
            a = tk.Toplevel()
            a.minsize('450', '500')
            a['bg'] = 'white'
            #a.overrideredirect(True)
            msg = f"""# Данные файлы не были добавлены, так как уже отслеживаются: #"""
            text = tk.Text(a, wrap=tk.WORD)
            text.insert(tk.INSERT, '#'*len(msg)+'\n'+msg+'\n'+'#'*len(msg)+'\n')
            for i in errors:
                text.insert(tk.INSERT, f'HOST {i}:\n')
                text.insert(tk.INSERT, '\n'.join(errors[i]))
            text.configure(state='disabled')
            text.pack(side=tk.LEFT, fill=tk.BOTH, expand=tk.YES)
            # scroll = tk.Scrollbar(command=text.yview)
            # scroll.grid(row=0, column=1, sticky='ns')
            # # scroll.pack(side=tk.LEFT, fill=tk.Y)
            # text.config(yscrollcommand=scroll.set)
            #tk.Label(a, text=msg).pack(expand=tk.YES, fill=tk.BOTH)
            # a.bell()
            #a.after(15000, lambda: a.destroy())
            return False
        else:
            showinfo('Успешно', 'Выбранные файлы успешно добавлены')
            return True

    def toggle_1(self, parent):
        if self.var.get() == 'Unlocked':
            for i in self.tree.get_children(parent):
                if self.tree.tag_has('disabled', i):
                    self.tree.tag_del(i, 'disabled')
                    self.toggle_1(i)
        else:
            for i in self.tree.get_children(parent):
                if not self.tree.tag_has('disabled', i):
                    self.tree.tag_add(i, 'disabled')
                    self.toggle_1(i)

    def toggle(self):   # TODO Recursion!
        for i in self.parent_nodes:
            self.toggle_1(self.parent_nodes[i])


class MyClienthandler(socketserver.BaseRequestHandler):

    def __init__(self, request, client_address, server):
        self.client_ip, self.client_port = client_address
        self.salt = secrets.token_bytes(16)
        self.check_sum = 0
        super().__init__(request, client_address, server)

    def auth2(self):
        self.request.settimeout(60)
        clients[self.client_ip] = []
        information = 'checksum_md5(sys.argv[0], salt=salt)'
        salt_msg = pickle.dumps(('salt', self.salt, foo))  # TODO +в словарь с именами потоков,+другую соль
        self.check_sum = checksum_md5('/home/user/Projects/checker/code/wtchdog.py', salt=self.salt)
        check_sum2 = checksum_sha('/home/user/Projects/checker/code/wtchdog.py', salt=self.salt)
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
                if data[1] == self.check_sum and data[2] == check_sum2:
                    break
                else:
                    output_1 = f'Client send {data[2]}'
                    output_2 = f'Server stored {self.check_sum}'
                    max_len = max(len(output_1), len(output_2))
                    print(f'[{self.client_address}] {"Auth failed!".upper()}\n'
                          f'[{self.client_address}] {output_1:>{max_len}}\n'
                          f'[{self.client_address}] {output_2:>{max_len}}', file=sys.stderr)
                    print('Connection close')
                    return 'AUTH FAILED'
        print(f'[{self.client_address} {threading.currentThread()}] Successful authorization. Key = {self.salt}')
        return 'SUCCESS AUTH'

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
        if self.client_ip not in ALLOWED_HOSTS:
            self.request.close()
            exit(0)
        b.start_up(self.client_ip)
        try:
            auth = self.auth2()
        except TimeoutError:
            auth = 'AUTH FAILED'

        if auth == 'AUTH FAILED':
            self.request.close()
        elif auth == 'SUCCESS AUTH':
            try:
                th = threading.Thread(target=self.send_com, name=self.client_ip + '_sender')
                th.daemon = True
                th.start()
                while True:
                    data = self.request.recv(409600)  # TODO Похоже, что блокирует цикл
                    if not data:
                        break
                    #print(data)
                    ans = pickle.loads(data)
                    #print(ans)
                    if ans[0] == 'KEEP-ALIVE':
                        if ans[2] == self.check_sum and ans[3] == self.salt:
                            reply = pickle.dumps(('info', 'OK KEEP-ALIVE', now()))
                            self.request.send(reply)
                        else:
                            reply = pickle.dumps(('CRITICAL ERROR', now(), self.check_sum, self.salt))
                            self.request.send(reply)
                            print(f'[CRITICAL] Received hashsum from {self.client_address} isn`t correct:\n'
                                  f'Server stored {self.check_sum}\nClient sent   {ans[2]}', file=sys.stderr)
                    elif ans[0] in INFO:  # TODO if 'ok', .., if not ok
                        print(ans)
                    elif ans[0] in sent:
                        if ans[1] == 'OK':
                            print(f'[{self.client_ip} RESPONSE]: ', ans)
                            resp[self.client_ip] = ans
                            sent.remove(ans[0])  # TODO Валидация очереди
                        else:
                            print(f'[{self.client_ip} RESPONSE]: ', ans)
                            sent.remove(ans[0])
            finally:
                self.request.close()
                print('close connection')
                print(f'[CRITICAL] lost connection with {self.client_address}', file=sys.stderr)

    def send_com(self):
        conn = self.request
        while True:
            cmd_list = clients[self.client_address[0]]
            # print(cmd_list, threading.currentThread().name)
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
