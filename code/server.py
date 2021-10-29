#!/home/dmitry/Projects/checker/env/bin/python
# -*- coding: utf-8 -*-
import argparse
import hashlib
import os.path
import signal
import socketserver, time
import sqlite3
from functools import reduce
from pathlib import PurePosixPath
import pickle
import sys
import threading
import secrets
import tkinter as tk
import tkinter.ttk as ttk
from tkinter.messagebox import *
from typing import Dict, Any

import gui.main
import gui.tree2
cnt = 0

myHost = ""
myPort = 50007
INFO = ["WARNING-CHANGES"]
ALLOWED_HOSTS = {
    "127.0.0.1": "ghost1",
}
CONNECTED_HOSTS = {}
HOSTS_UNDER_CONTROL = {}
CONFIG_FILE = "/home/dmitry/Projects/checker/code/files/psv-config.txt"
database = "mydatabase.db"
startup = dict()

clients = {}
resp: Dict[Any, Any] = {}


def sigusr1_handler(self, signum, frame):
    # self.parent.update()
    # self.parent.grab_set()
    # self.parent.focus_set()
    print('hi')
    # self.parent.deiconify()
    # self.parent.update()
    # self.parent.grab_set()
    # self.parent.focus_set()

def now():
    return time.ctime(time.time())


def time_of_func_running(func):
    def wrapped(*args, **kwargs):
        start_time = time.perf_counter()
        res = func(*args, **kwargs)
        debugger(f"Выполнение функции {str(func)} заняло {time.perf_counter()-start_time} секунд.")
        return res
    return wrapped


def debugger(*args, **kwargs):
    """ Replace to logger.logger """
    if namespace.debug:
        print(*args, **kwargs)


def createParser():
    """Парсер аргументов командной строки
    """
    pars = argparse.ArgumentParser()
    #pars.add_argument('path')
    pars.add_argument('-d', '--debug', action='store_true', default=False)
    return pars


def valid_ipv4(ip):
    lst = ip.split(".")
    if len(lst) != 4:
        return False
    for i in lst:
        if int(i) > 255 or int(i) < 0:
            return False
    return True


def checksum_md5(filename, salt=None):
    md5 = hashlib.md5()
    with open(filename, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            md5.update(chunk)
            if salt:
                md5.update(salt)
    return md5.hexdigest()


def checksum_sha(filename, salt=None):
    sha = hashlib.sha256()
    with open(filename, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
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


def main_thread():
    global a
    sqlite3.enable_callback_tracebacks(True)
    a = serverUI()
    a.tree = Tree(a.parent, "")
    a.tree.load_config()
    a.tree.load_tree()
    # signal.signal(signal.SIGUSR1, a.sigusr1_handler)
    tk.mainloop()


def _main_thread():
    while True:
        client, *cmd = tuple(x for x in input().strip().split())
        if client in clients:
            debugger("[MAIN THREAD]: cmd added")
            clients[client].append(("cmd",) + tuple(cmd))
        elif client.lower() == "exit":
            break
        else:
            debugger(f"This client {client} not found")


class serverUI(gui.main.UI):
    def __init__(self):
        self.tree = None
        super().__init__()

    @staticmethod
    @time_of_func_running
    def get_list(flag=None, client=None):
        answer = {}
        q = list()
        timeout = 30
        if client:
            for client_ in client:
                clients[client_].append(("cmd", "get_watchlist", "0"))
                q.append(client_)
        else:
            for client in clients:
                clients[client].append(("cmd", "get_watchlist", "0"))
                q.append(client)
        while q and timeout > 0:
            for i in q:
                for response in resp[i]:
                    if ("cmd", "get_watchlist", "0") in response:
                        answer[i] = response[2]
                        resp[i].remove(response)
                        q.remove(i)
            time.sleep(0.05)
            timeout -= 0.05
        if flag:
            return answer
        output = [str(i) + ": " + str(answer[i]) for i in answer]
        showinfo("list", "\n".join(output))

    def add_file(self):
        pass

    @time_of_func_running
    def get_checked(self):
        lst = self.tree.get_checked()
        showinfo("checked", str(lst))

    def add_host(self, ip, name):

        for _ip in self.tree.config:
            if self.tree.config[_ip]['name'] == name:
                return False, _ip, name

        if ip not in self.tree.config:
            self.tree.config[ip] = {"name": name, "watched_files": [], 'md5': {}}
            # ALLOWED_HOSTS[ip] = name
            self.tree.save_config()
            conn = sqlite3.connect(database)
            cur = conn.cursor()
            data = (name, ip, time.time())
            cur.execute(
                """INSERT INTO ghosts(name, ip, time) 
            VALUES(?, ?, ?);""",
                data,
            )
            conn.commit()
            conn.close()

            return True, ip, name
        else:
            return False, False, self.tree.config[ip]['name']


class Tree(gui.tree2.App):
    load_status = 0
    cnt = 0

    def make_load_gif(self):

        label = tk.Label(self.frame)
        label.place(anchor='center', relx=0.5, rely=0.5)
        frameCnt = 15
        frames = [tk.PhotoImage(file='/home/dmitry/Загрузки/XOsX.gif', format='gif -index %i' % i).subsample(3, 3) for i in range(frameCnt)]

        def update(ind):
            debugger(f'update start {ind=}')
            if self.load_status == 1:
                debugger('load status = 1! Download complete')
                label.place_forget()
                return
            frame = frames[ind]
            ind += 1
            if ind == frameCnt:
                ind = 0
            label.configure(image=frame, bg='white')
            self.frame.update()
            self.frame.after(100, update, ind)
        update(0)

    def start_up(self, client_ip):
        startup[client_ip] = True
        abspath = "/"
        if client_ip not in self.nodes:
            self.nodes[client_ip] = {}
        self.dirs[client_ip] = []
        self.node[client_ip] = {}
        self.path[client_ip] = {}
        debugger("[SAVED NODE]", self.saved_node)
        self.make_load_gif()
        if client_ip in self.saved_node:
            for item in self.saved_node[client_ip]:
                try:
                    self.tree.delete(item[1])
                except Exception as e:
                    debugger('Item: ', item)
                    debugger(f"[ERROR start_up] {e}")
                    pass
                # self.tree.tag_del(self.saved_node[i][path], 'disconnected')
        node = self.tree.insert(
            "",
            "end",
            text=f' {self.config[client_ip]["name"]}',
            open=False,
            values=("подключен", "целостность не нарушена", "отслеживается"),
        )

        self.nodes[client_ip][node] = abspath
        self.node[client_ip][node] = abspath
        self.path[client_ip][abspath] = node

        self.parent_nodes[client_ip] = node
        self.tree.tag_add(node, client_ip)
        self.tree.tag_add(node, "ghost")

        watch_list = serverUI.get_list(flag=True, client=(client_ip,))
        diff = {client_ip: {"to_add": [], "to_remove": []}}

        for file in watch_list[client_ip]:
            """ на случай, если какой-то файл отслеживается клиентом, но в конфиге сервера его нет
            """
            # conn, cur = False, False
            if file not in self.config[client_ip]["watched_files"]:
            #     if not conn:
            #         conn = sqlite3.connect(database)
            #         cur = conn.cursor()
            #     data = (self.config[client_ip]['name'], file, )
            #     cur.execute("INSERT INTO watched_files(ghost, path, md5, time) VALUES(?, ?, ?, ?)", data)
                self.config[client_ip]["watched_files"].append(file)

        for file in self.config[client_ip]["watched_files"]:
            if file not in watch_list[client_ip]:
                diff[client_ip]["to_add"].append(file)
                debugger(
                    f"[WARNING] File {file} from {client_ip} is not watching by client, but stored in server config"
                )

        self.save_config()
        self.send_files(diff, start_up=True)
        self._load_tree(
            self.backup_tree[client_ip],
            node,
            client_ip,
            "/",
            open=True,
            disconnect=False,
        )
        if not self.backup_tree[client_ip]:
            self.tree.insert(
                node,
                "end",
                text=" ",
                open=False,
            )
        startup[client_ip] = False
        self.checked_node = [node for node in self.tree.get_checked()]
        self.tree.saved_node = self.checked_node # TODO Исправить
        self.load_status = 1
        debugger('start_up done')

        debugger(self.bind_func_id)

    def _config_from_file(self):
        pass

    def config_from_file(self):
        try:
            with open(CONFIG_FILE, "rb") as f:
                self.config = pickle.load(f)
        except Exception as e:
            debugger("EXCEPTION: ", e)
        print("config 1", self.config)

    def load_config(self):
        HOSTS = {}
        local_config = {}
        conn = sqlite3.connect(database)
        cur = conn.cursor()
        sql = "SELECT name, ip FROM ghosts"

        if not self.config:
            self.backup_tree = {}

        for ip_row in cur.execute(sql):
            name, ip = ip_row
            HOSTS[name] = ip
        conn.commit()

        for host in HOSTS:
            ip = HOSTS[host]
            watched_files = []
            _hash = {}
            for data in cur.execute("SELECT path, md5 FROM watched_files WHERE ghost=?", (host, )):
                path, md5 = data
                _hash[path] = md5
                watched_files.append(path)

            local_config[ip] = {'name': host, 'watched_files': watched_files[:], 'md5': _hash}

        self.config = local_config
        print(f'{self.config=}')
        conn.commit()
        conn.close()

        for host_ip in self.config:
            self.backup_tree[host_ip] = {}
            paths = self.config[host_ip]["watched_files"]
            for path in map(PurePosixPath, paths):
                reduce(
                    lambda node, part: node.setdefault(part, {}),
                    path.parts[1:],
                    self.backup_tree[host_ip],
                )

    def load_tree(self):
        for host_ip in self.backup_tree:
            name = self.config[host_ip]["name"]
            text_with_space = f' {name}'
            node = self.tree.insert(
                "", "end", text=text_with_space, open=True, value=("NOT_CONNECTED", "-", "-")
            )
            self.tree.tag_add(node, host_ip)
            self.nodes[host_ip] = {}
            self.node[host_ip] = {}
            self.path[host_ip] = {}
            self.saved_node[host_ip] = [("/", node)]


            if self.var.get() == "Locked":
                self.tree.tag_add(node, "disabled")
            self.tree.change_state(node, "tristate")
            self.tree.tag_add(node, "disconnected")
            self.tree.tag_add(node, host_ip)
            self._load_tree(self.backup_tree[host_ip], node, host_ip, "/")

    def _load_tree(self, parent, iid, host_ip, abspath_, open=True, disconnect=True):
        for i in parent:
            abspath = abspath_ + "/" + i
            text = i
            text_with_space = f' {text}'
            if abspath in self.config[host_ip]['md5']:
                md5 = self.config[host_ip]['md5'][abspath]
                node = self.tree.insert(
                    iid,
                    "end",
                    text=text_with_space,
                    open=open,
                    value=('', md5, '')
                )
            else:
                node = self.tree.insert(
                    iid,
                    "end",
                    text=text_with_space,
                    open=open,
                )
            self.saved_node[host_ip].append((abspath, node))
            self.tree.tag_add(node, host_ip)
            if self.var.get() == "Locked":
                self.tree.tag_add(node, "disabled")
            if disconnect:
                self.tree.tag_add(node, "disconnected")
            self.tree.change_state(node, "tristate")
            self.tree.tag_add(node, host_ip)
            self.node[host_ip][node] = abspath
            self.path[host_ip][abspath] = node

            if not len(parent[i]):
                self.tree.change_state(node, "checked")
                abspath = abspath_

                self.checked_node.append(node)
            else:
                self.nodes[host_ip][node] = abspath
            self._load_tree(
                parent[i], node, host_ip, abspath, open=open, disconnect=disconnect
            )

        abspath = "/"


    @time_of_func_running
    def listdir(self, abspath, client="127.0.0.1"):
        timeout = 10
        debugger('clients in listdir', clients)
        clients[client].append(("cmd", "get_listdir", abspath))

        while timeout > 0:
            debugger(timeout)
            time.sleep(0.2)
            timeout -= 0.2

            for response in resp[client]:
                try:
                    if ("cmd", "get_listdir", abspath) == response[0]:
                        for i in response[2]:
                            if response[2][i]:
                                self.dirs[client].append(i)
                        resp[client].remove(response)
                        return response[2]
                    else:
                        continue
                except Exception as e:
                    debugger("[ERROR listdir]", e)
                    return "FAIL"
        return ["..."]  # TODO call timeout error message

    def update(self, client, path="/"):
        node = self.tree.insert("", "end", text=client, open=False)
        self.insert_node(node, path, path)

    @time_of_func_running
    def send_checked(self):
        # client = '127.0.0.1'  # TODO Перенести в main app? Убрать лишние запросы на листы отсдеживания
        checked = self.get_checked()  # TODO add many clients (almost done)
        # TODO тут короче все надо перепахать
        debugger(f"[DEBUG] checked={checked}")
        current_watchdict = serverUI.get_list(flag=True)
        errors = {}
        old_watchdict = {}
        for client in clients:
            if client not in checked:
                debugger("RM ALL ", client)
                cmd = ("cmd", "rm_all", "0")
                clients[client].append(cmd)
                continue

            for file in self.config[client]["watched_files"]:
                debugger("file", file)
                if file not in checked[client]:
                    debugger("file to remove ", file)
                    cmd = ("cmd", "rm", file)
                    clients[client].append(cmd)
            for file in current_watchdict[client]:
                if file not in checked[client]:
                    debugger("file to remove ", file)
                    cmd = ("cmd", "rm", file)
                    clients[client].append(cmd)

        for client in checked:
            for i in checked[client]:
                path = os.path.normpath(i)
                debugger("path to add", path)
                if i not in current_watchdict[client]:
                    cmd = ("cmd", "add", path)
                    clients[client].append(cmd)
                else:
                    if client not in errors:
                        errors[client] = [path]
                    else:
                        errors[client].append(path)
            """for i in current_watchdict[client]:
                path = os.path.normpath(i)
                print('path to remove', path)
                cmd = ('cmd', 'rm', path)
                clients[client].append(cmd)
                print('очередь ', clients[client])"""
        debugger("очередь ", clients)
        self.save_checked()
        if errors:
            a = tk.Toplevel(self.master)
            a.minsize("450", "500")
            a["bg"] = "white"
            # a.overrideredirect(True)
            msg = f"""# Данные файлы не были добавлены, так как уже отслеживаются: #"""
            text = tk.Text(a, wrap=tk.WORD)
            text.insert(tk.INSERT, "#" * len(msg) + "\n" + msg + "\n" + "#" * len(msg))
            for i in errors:
                text.insert(tk.INSERT, f"\nHOST {i}:\n")
                text.insert(tk.INSERT, "\n".join(errors[i]))
            text.configure(state="disabled")
            text.pack(side=tk.LEFT, fill=tk.BOTH, expand=tk.YES)
            a.transient(self.master)
            # self.dialog.lift()
            a.grab_set()
            a.focus_set()
            a.wait_window()
            return False
        else:
            showinfo("Успешно", "Выбранные файлы успешно добавлены")
            return True

    @time_of_func_running
    def get_diff(self):
        selected_items = self.get_checked()  # TODO Починить
        diff = {}
        for client in selected_items:
            diff[client] = {"to_remove": [], "to_add": []}
            current_watch_list = self.config[client]["watched_files"]
            changed_watch_list = selected_items[client]
            to_remove = []
            to_add = []
            for file in current_watch_list:
                if file not in changed_watch_list:
                    to_remove.append(file) #####
            to_remove = list(set(to_remove))####
            for file in changed_watch_list:
                if file not in current_watch_list:
                    to_add.append(file)
            to_add = list(set(to_add))####
            if not changed_watch_list:
                to_remove = "ALL"
            diff[client]["to_add"] = to_add
            diff[client]["to_remove"] = to_remove
        return diff

    def make_change_window(self):
        counter = 0
        add_counter = 0
        rm_counter = 0
        diff = self.get_diff()
        window = tk.Toplevel(self.master)
        window.geometry("1000x800")
        window.minsize("850", "300")
        #window.resizable(width=False, height=False)
        window.grid_columnconfigure(0, weight=1)
        window.grid_rowconfigure(0, weight=1)
        frame = ttk.Frame(window, style='Card.TFrame')
        frame.grid(sticky=tk.NSEW)
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(0, weight=1)

        self.text_to_display = []
        #bg = self.master.cget("background")
        text_frame = tk.Text(frame, wrap=tk.WORD, bd=5, highlightthickness=0, relief='flat')
        self.text_frame = text_frame

        for client in diff:
            text = client + ":\n"
            text_frame.insert(tk.INSERT, text)
            for file in diff[client]["to_add"]:
                text = "[ADD FILE]\t" + file + " \n"
                self.text_to_display.append(text)
                add_counter += 1
            for file in diff[client]["to_remove"]:
                text = "[RMV FILE]\t" + file + " \n"
                self.text_to_display.append(text)
                rm_counter += 1
            for text in self.text_to_display:
                text_frame.insert(tk.INSERT, text)
        counter = add_counter + rm_counter

        text_frame.grid(row=0, column=0, columnspan=2, sticky=tk.NSEW)
        text_frame.grid_columnconfigure(0, weight=1)
        text_frame.grid_rowconfigure(0, weight=1)
        text_frame.configure(state="disabled")
        text_frame.tag_config("OK", foreground="green")
        text_frame.tag_config("ERROR", foreground="red")

        separator = ttk.Separator(frame, orient='horizontal')
        separator.grid(row=1, column=0, columnspan=2, sticky="NWE")

        button_ok = ttk.Button(frame, style='Accent.TButton')
        button_ok.config(
            text="Accept", command=lambda: self.send_files(diff, button=button_ok),
        )
        button_ok.grid(row=1, column=0, sticky="wn", ipady=2, ipadx=3, pady=5, padx=5)

        self.pb = ttk.Progressbar(frame, orient="horizontal", length=700, mode="determinate")
        self.pb.grid(row=1, column=0, sticky='ws', pady=5, padx=5)
        self.pb.grid_columnconfigure(0, weight=1)
        self.pb.grid_rowconfigure(0, weight=1)
        self.pb['value'] = 0
        self.pb['maximum'] = counter

        self.pb_label = ttk.Label(frame, text='')
        self.pb_label.grid(row=1, column=1, sticky='n', pady=5, padx=5)

        self.info_label = ttk.Label(frame, text='')
        self.info_label.grid(row=1, column=1, sticky='wn', pady=5, padx=5)
        self.info_label.configure(text=f'Hosts: {len(diff)}\nTo add: {add_counter}\nTo remove: {rm_counter}')

        scroll = ttk.Scrollbar(frame, command=text_frame.yview)
        scroll.grid(row=0, column=1, sticky='ens', padx=0, pady=2)
        text_frame.config(yscrollcommand=scroll.set)

        self.pb.grid_remove()
        window.transient(self.master)
        # self.dialog.lift()
        window.grab_set()
        window.focus_set()
        window.wait_window()

    def send_files(self, diff, start_up=False, button=None):

        start = time.time()
        if button:
            button.configure(state='disabled')
            button.grid_remove()
            self.pb.grid()
            self.info_label.grid_forget()
            self.info_label.grid(row=1, column=0, sticky='wn', pady=5, padx=5)

        TIMEOUT = 30
        TRY = 3
        retry = TRY
        count = 0
        debugger("Send files. Diff: ", diff)
        send = {}
        received = {}
        buff = {}
        wait_to_remove = {}
        delete_from_db = []
        insert_into_db = []
        value, maximum = None, None
        lock = threading.Lock()
        lock1 = threading.Lock()


        while retry > 0:
            if not send:
                # lock.acquire()
                for client in diff:
                    send[client] = []
                    buff[client] = []
                    received[client] = []
                    # wait_to_remove[client] = []

                    for file in diff[client]["to_add"]:
                        cmd = ("cmd", "add", file)
                        send[client].append(cmd)
                        buff[client].append(cmd)
                        clients[client].append(cmd)
                        count += 1
                    for file in diff[client]["to_remove"]:
                        cmd = ("cmd", "rm", file)
                        send[client].append(cmd)
                        buff[client].append(cmd)
                        clients[client].append(cmd)
                        count += 1
                # lock.release()
            else:
                # lock.acquire()
                with open('log_psv.txt', 'w') as f:
                    f.write(f'[########] RETRY {retry} [#############]\n')
                    f.write(f'[state]\nОчередь: {clients}\nОтправлено: {send}\n Принято: {received}\n')
                    for client in send:
                        f.write(f'\n[]]\n')
                        for cmd in send[client]:
                            if cmd not in received[client]:
                                clients[client].append(cmd)
                                f.write(f'[REPEAT TO {client}] {cmd}\n')
                # lock.release()
            timeout = TIMEOUT
            #time.sleep(1)
            while timeout > 0 and count:
                debugger(f'time left: {timeout}, files left: {count}')
                debugger("SEND: ", send)
                time.sleep(0.05)
                timeout -= 0.05
                for client in diff:
                    # lock1.acquire()
                    # if wait_to_remove[client]:
                        # lock1.acquire()
                        # print('block')
                    # for rsp in wait_to_remove[client]:
                        # print('rsp in block ', rsp)
                        # resp[client].remove(rsp)
                        # wait_to_remove[client].remove(rsp)
                        # send[client].remove(rsp[0])
                        # lock1.release()
                    response = resp[client]  # TODO ????????
                    # lock1.release()
                    try:
                        # intersection = [i for i in response[0] if i in send]
                        for rsp in response:
                            #print('response', response)
                            debugger('rsp', rsp)
                            sent_cmd = rsp[0]
                            if sent_cmd in send[client]:
                                debugger('True')
                                # lock.acquire()
                                response.remove(rsp)
                                # wait_to_remove[client].append(rsp)
                                received[client].append(sent_cmd)
                                #send[client].remove(sent_cmd)
                                # lock.release()

                                count -= 1
                                abspath = rsp[0][2]
                                if rsp[1] == 'OK':

                                    # conn = sqlite3.connect(database)
                                    # cur = conn.cursor()

                                    if rsp[0][1] == "add":
                                        if (
                                            abspath
                                            not in self.config[client]["watched_files"]
                                        ):
                                            self.config[client]["watched_files"].append(
                                                abspath
                                            )
                                            data = (self.config[client]['name'], abspath, rsp[2], time.time())
                                            insert_into_db.append(data)
                                            # cur.execute("INSERT INTO watched_files(ghost, path, md5, time) VALUES(?, ?, ?, ?)", data)
                                            # conn.commit()
                                            message = "\tSuccessfully added to watch!" # TODO Много одинакового кода
                                            node = self.path[client][abspath]
                                            self.tree.item(node, value=('OK', rsp[2], 'отслеживается'))
                                            self.master.update()
                                        else:
                                            """ """
                                            debugger("[DEBUG POINT send_files 1] UNEXPECTED ERROR!")
                                            message = "[SYNC ERROR] This file already watching ."

                                    else:

                                        if abspath in self.config[client]["watched_files"]:
                                            self.config[client]["watched_files"].remove(
                                                abspath
                                            )
                                            message = "\tSuccessfully removed from watch!"

                                            data = (self.config[client]['name'], abspath)
                                            delete_from_db.append(data)
                                            # cur.execute(
                                            #     "DELETE FROM watched_files WHERE ghost=? AND path=?",
                                            #     data)
                                            # conn.commit()
                                            # print('remove commit')

                                        else:
                                            debugger("[DEBUG POINT send_files 2] UNEXPECTED ERROR!")
                                            message = "[SYNC ERROR] This file already is not watching."


                                elif rsp[2] == 'FileNotFoundError':
                                    message = 'Error! This file does not exist (client send FileNotFoundError). ' \
                                              'File removed from tree'
                                    debugger(self.path)
                                    debugger(message)

                                    if abspath in self.config[client]['watched_files']:
                                        debugger(f'REMOVE file from config file = {abspath}')
                                        self.config[client]['watched_files'].remove(abspath)

                                        data = (self.config[client]['name'], abspath)
                                        delete_from_db.append(data)

                                    if abspath in self.path[client]:
                                        node = self.path[client][abspath]
                                        self.tree.detach(node)
                                        # self.tree.change_state(node, 'unchecked')

                                elif rsp[2] == 'This file already watches':
                                    if sent_cmd in buff[client]:

                                        data = (self.config[client]['name'], abspath, rsp[2], time.time())
                                        insert_into_db.append(data)

                                        if (
                                            abspath
                                            not in self.config[client]["watched_files"]
                                        ):
                                            self.config[client]["watched_files"].append(
                                                abspath
                                            )

                                        message = "\tSuccessfully added to watch!" # todo rmv from scope
                                    else:
                                        message = 'Error! This file already watches'

                                elif rsp[2] == 'This file isn`t watching':
                                    if sent_cmd in buff[client]:

                                        data = (self.config[client]['name'], abspath)
                                        delete_from_db.append(data)

                                        if abspath in self.config[client]["watched_files"]:
                                            self.config[client]["watched_files"].remove(
                                                abspath
                                            )
                                        message = "\tSuccessfully removed from watch!"
                                    else:
                                        message = 'Error! This file isn`t watching'

                                else:
                                    message = rsp[2]
                                debugger('message: ', message)
                                #self.save_config()
                                #self.load_config()

                                if start_up:
                                    continue

                                maximum = int(self.pb['maximum'])
                                value = maximum - count
                                self.info_label.configure(text=f'[{client}] {abspath}')

                                self.pb_label.configure(
                                    text=f'Обработано {value} файлов из {maximum}\n '
                                         f'Осталось попыток: {retry}/{TRY}'
                                )

                                self.pb['value'] = value
                                if count == 0:
                                    self.pb_label.configure(
                                        text=f' ВЫПОЛНЕНО!\n '
                                             f'Обработано {value} файлов из {maximum}\n '
                                             f'Осталось попыток: {retry}/{TRY}'
                                    )

                                index = self.text_frame.search(abspath + ' ', "1.0", 'end')
                                self.text_frame.update()
                                self.text_frame.configure(state="normal")
                                if index:
                                    string = self.text_frame.get(f'{index} linestart', f'{index} lineend')
                                    print(f'{index=}, {abspath=}, {len(abspath)=}, {string=}, {len(string)=}')
                                    self.text_frame.insert(
                                        f"{index} lineend", f"\t{message.rjust(100 - len(string))}"
                                    )
                                    print(f"\t{message}".rjust(120-len(string)))
                                    print(string)
                                    if 'Error!' in message:
                                        self.text_frame.tag_add(
                                            'ERROR',
                                            f"{index} linestart",
                                            f"{index} lineend",
                                        )
                                    else:
                                        self.text_frame.tag_add(
                                            "OK",
                                            f"{index} linestart",
                                            f"{index} lineend",
                                        )
                                    self.text_frame.configure(state="disabled")
                                    self.text_frame.update()
                                else:
                                    debugger("Unexpected Error!")
                            else:
                                debugger(f'False {sent_cmd} not in send[client]')
                        else:
                            continue

                    except Exception as e:
                        debugger("[ERROR send_files]", e)
                        if insert_into_db or delete_from_db:
                            with sqlite3.connect(database) as conn:
                                cur = conn.cursor()
                                if insert_into_db:
                                    cur.executemany(
                                        "INSERT INTO watched_files(ghost, path, md5, time) VALUES(?, ?, ?, ?)",
                                        insert_into_db
                                    )
                                    conn.commit()
                                if delete_from_db:
                                    cur.executemany(
                                        "DELETE FROM watched_files WHERE ghost=? AND path=?",
                                        delete_from_db)
                                    conn.commit()
                        return "FAIL"
            if count == 0:
                debugger(f'send files working {time.time()-start}')

                if insert_into_db or delete_from_db:
                    with sqlite3.connect(database) as conn:
                        cur = conn.cursor()
                        if insert_into_db:
                            cur.executemany(
                                "INSERT INTO watched_files(ghost, path, md5, time) VALUES(?, ?, ?, ?)",
                                insert_into_db
                            )
                            conn.commit()
                        if delete_from_db:
                            cur.executemany(
                                "DELETE FROM watched_files WHERE ghost=? AND path=?",
                                delete_from_db)
                            conn.commit()
                return ['OK, DONE']
            retry -= 1
            if not start_up:
                self.pb_label.configure(
                    text=f'Обработано {value} файлов из {maximum}\n '
                         f'Осталось попыток: {retry}/{TRY}'
                         f'Потеряли: {len(send)}'
                )
                #time.sleep(1)
            debugger(f'[RETRYING #{retry}]')
        debugger(f'send files working {time.time() - start} But..')

        if insert_into_db or delete_from_db:
            with sqlite3.connect(database) as conn:
                cur = conn.cursor()
                if insert_into_db:
                    cur.executemany(
                        "INSERT INTO watched_files(ghost, path, md5, time) VALUES(?, ?, ?, ?)",
                        insert_into_db
                    )
                    conn.commit()
                if delete_from_db:
                    cur.execute(
                        "DELETE FROM watched_files WHERE ghost=? AND path=?",
                        delete_from_db)
                    conn.commit()
        return ["..."]  # TODO call timeout error message

    def save_config(self):
        with open(CONFIG_FILE, "wb") as f:
            pickle.dump(self.config, f)

    def save_checked(self):  # TODO fix to save_config
        selected = self.get_checked()
        for client_ip in selected:
            # client_name = ALLOWED_HOSTS[client_ip]
            client_name = self.config[client_ip]["name"]
            self.config[client_ip] = {
                "name": client_name,
                "watched_files": selected[client_ip],
            }

        self.checked_node = [node for node in self.tree.get_checked()]
        debugger('ggg checked_node: ', self.checked_node)
        self.save_config()

    #@time_of_func_running
    def toggle_1(self, parent):
        #cnt += 1
        self.cnt1()
        if self.var.get() == "Unlocked":
            # self.show_all()
            for i in self.tree.get_children(parent):
                if self.tree.tag_has("disabled", i):
                    self.tree.tag_del(i, "disabled")
                    self.toggle_1(i)
            # self.show_all()
        else:
            # self.show_only_selected()
            for i in self.tree.get_children(parent):
                if not self.tree.tag_has("disabled", i):
                    self.tree.tag_add(i, "disabled")
                    self.toggle_1(i)
            # self.show_only_selected()

    @time_of_func_running
    def toggle(self):  # TODO Recursion!
        #cnt = 0
        #print('checked_node: ', self.checked_node)
        for i in self.parent_nodes:
            #cnt += 1
            self.toggle_1(self.parent_nodes[i])
        debugger(f'Количество итераций функции toggle: {self.cnt}')
        self.cnt = 0

    def new_toggle(self):
        pass

    def cnt1(self):
        self.cnt += 1


class MyClienthandler(socketserver.BaseRequestHandler):
    def __init__(self, request, client_address, server):
        self.client_ip, self.client_port = client_address
        self.salt = secrets.token_bytes(16)
        self.check_sum = 0
        super().__init__(request, client_address, server)

    def auth2(self):
        self.request.settimeout(60)
        clients[self.client_ip] = []
        resp[self.client_ip] = []
        information = "checksum_md5(sys.argv[0], salt=salt)"
        salt_msg = pickle.dumps(
            ("salt", self.salt, foo)
        )  # TODO +в словарь с именами потоков,+другую соль
        self.check_sum = checksum_md5(
            "/home/dmitry/Projects/checker/code/wtchdog.py", salt=self.salt
        )
        check_sum2 = checksum_sha(
            "/home/dmitry/Projects/checker/code/wtchdog.py", salt=self.salt
        )
        if self.client_ip == "192.168.192.130":
            self.check_sum = checksum_md5(
                "/home/midway/NIRS/code/work/code/files/1.py", salt=self.salt
            )
            check_sum2 = checksum_sha(
                "/home/midway/NIRS/code/work/code/files/1.py", salt=self.salt
            )
        debugger(f"[CONNECTION REQUEST {self.client_ip}:{self.client_port}] at {now()}")
        debugger(f"[AUTH DATA] SALT = {self.salt} CHECK_SUM = {self.check_sum}")
        while True:
            data = pickle.loads(self.request.recv(1024))
            if data[0] == "ready to auth":
                self.request.send(salt_msg)
            elif data[0] == self.salt:
                if data[1] == self.check_sum and data[2] == check_sum2:
                    break
                else:
                    output_1 = f"Client send {data[2]}"
                    output_2 = f"Server stored {self.check_sum}"
                    max_len = max(len(output_1), len(output_2))
                    debugger(
                        f'[{self.client_address}] {"Auth failed!".upper()}\n'
                        f"[{self.client_address}] {output_1:>{max_len}}\n"
                        f"[{self.client_address}] {output_2:>{max_len}}",
                        file=sys.stderr,
                    )
                    debugger("Connection close")

                    return "AUTH FAILED"
        debugger(
            f"[{self.client_address} {threading.currentThread()}] Successful authorization. Key = {self.salt}"
        )
        return "SUCCESS AUTH"

    def auth(self):
        self.request.settimeout(60)
        clients[self.client_ip] = []
        salt_msg = pickle.dumps(
            ("salt", self.salt)
        )  # TODO добавить в словарь с именами потоков
        self.check_sum = checksum_md5(
            "/home/dmitry/Projects/checker/code/wtchdog.py", salt=self.salt
        )
        if self.client_ip == "192.168.192.130":
            check_sum = checksum_md5(
                "/home/midway/NIRS/code/work/code/files/1.py", salt=self.salt
            )

        debugger(f"[CONNECTION REQUEST {self.client_ip}:{self.client_port}] at {now()}")
        debugger(f"[AUTH DATA] SALT = {self.salt} CHECK_SUM = {self.check_sum}")
        while True:
            data = pickle.loads(self.request.recv(1024))
            # print(data)
            if data[0] == "ready to auth":
                self.request.send(salt_msg)
            elif data[0] == self.salt:
                if data[1] == self.check_sum:
                    break
                else:
                    output_1 = f"Client send {data[1]}"
                    output_2 = f"Server stored {self.check_sum}"
                    max_len = max(len(output_1), len(output_2))
                    debugger(
                        f'[{self.client_address}] {"Auth failed!".upper()}\n'
                        f"[{self.client_address}] {output_1:>{max_len}}\n"
                        f"[{self.client_address}] {output_2:>{max_len}}",
                        file=sys.stderr,
                    )
                    debugger("Connection close")
                    return "AUTH FAILED"
        debugger(
            f"[{self.client_address} {threading.currentThread()}] Successful authorization. Key = {self.salt}"
        )
        return "SUCCESS AUTH"

    def handle(self) -> None:
        sent = []
        locker = threading.Lock()
        if self.client_ip not in a.tree.config:
            self.request.close()
            exit(0)
        try:
            auth = self.auth2()
        except TimeoutError:
            auth = "AUTH FAILED"

        if auth == "AUTH FAILED":
            self.request.close()
        elif auth == "SUCCESS AUTH":
            try:
                th = threading.Thread(
                    target=self.send_com, name=self.client_ip + "_sender", args=(sent,)
                )
                th.daemon = True
                th.start()
                thread_start_up = threading.Thread(
                    target=a.tree.start_up, args=(self.client_ip,)
                )
                thread_start_up.daemon = True
                thread_start_up.start()
                while True:
                    data = self.request.recv(40960*5)
                    if not data:
                        continue
                    ans = pickle.loads(data)
                    debugger(f'[ROW RESPONSE FROM {self.client_ip}]: {ans}')
                    if ans[0] == 'event':
                        """(event, (ip, port), file, md5, time, event_type)"""

                        with sqlite3.connect('mydatabase.db') as conn:
                            cur = conn.cursor()
                            host_name = a.tree.config[self.client_ip]['name']
                            #host_name from response
                            values = (host_name, *ans[2:])
                            cur.execute("INSERT INTO events(ghost, file, md5, time, event_type) VALUES(?, ?, ?, ?, ?)", values)
                            conn.commit()

                        while startup[self.client_ip]:
                            print('startup flag', startup)
                            time.sleep(0.1)
                        node = a.tree.path[self.client_ip][ans[2]]
                        a.tree.tree.item(node, value=('ФАЙЛ ИЗМЕНЕН!', ans[3], time.ctime(float(ans[4]))))
                        a.tree.tree.tag_add(node, "changed")
                        a.tree.tree.master.update()

                    if ans[0] == "KEEP-ALIVE":
                        if ans[2] == self.check_sum and ans[3] == self.salt:
                            reply = pickle.dumps(("info", "OK KEEP-ALIVE", now()))
                            clients[self.client_ip].append(reply)
                            # self.request.send(reply)
                        else:
                            reply = pickle.dumps(
                                ("CRITICAL ERROR", now(), self.check_sum, self.salt)
                            )
                            clients[self.client_ip].append(reply)
                            # self.request.send(reply)
                            debugger(
                                f"[CRITICAL] Received hashsum from {self.client_address} isn`t correct:\n"
                                f"Server stored {self.check_sum}\nClient sent   {ans[2]}",
                                file=sys.stderr,
                            )
                    # elif ans[0] in INFO:  # TODO if 'ok', .., if not ok
                        # print(ans)
                    elif ans[0] in sent:
                        if ans[1] == "OK":
                            debugger(f"[{self.client_ip} RESPONSE]: ", ans)
                            # locker.acquire()
                            resp[self.client_ip].append(ans)  # todo queue
                            # locker.release()
                            sent.remove(ans[0])  # TODO Валидация очереди
                        else:
                            debugger(f"[{self.client_ip} RESPONSE]: ", ans)
                            # locker.acquire()

                            resp[self.client_ip].append(ans)  # todo remove!!!!
                            # locker.release()
                            sent.remove(ans[0])
            finally:
                self.request.close()
                debugger("close connection")
                debugger(
                    f"[CRITICAL] lost connection with {self.client_address}",
                    file=sys.stderr,
                )

    def send_com(self, sent):
        conn = self.request
        while True:
            cmd_list = clients[self.client_address[0]]
            # print(cmd_list, threading.currentThread().name)
            # print('cmd list', cmd_list)
            for i in cmd_list:
                reply = pickle.dumps(i)
                conn.send(reply)
                sent.append(i)
                cmd_list.remove(i)
                debugger(f"send from server to client: {i}")
                time.sleep(0.05)
                # print(cmd_list)
            time.sleep(0.5)


parser = createParser()
namespace = parser.parse_args()


myaddr = (myHost, myPort)
server = socketserver.ThreadingTCPServer(myaddr, MyClienthandler)
server_thread = threading.Thread(target=server.serve_forever)
server_thread.name = "server_thread"
server_thread.daemon = True
server_thread.start()
debugger("Server loop running in thread:", server_thread.name)
try:

    main_thread()
finally:
    server.server_close()
    debugger("close server")
