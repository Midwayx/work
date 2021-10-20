#!/home/dmitry/Projects/checker/env/bin/python
# -*- coding: utf-8 -*-
import argparse
import sys
import time
import logging
import os
from watchdog.observers import Observer
from watchdog.events import LoggingEventHandler, FileSystemEventHandler, FileSystemEvent
import sqlite3
import hashlib
import socket
import pickle
import threading

serverHost = "localhost"
serverPort = 50007
sockobj = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sockobj.connect((serverHost, serverPort))

sent = []
wait_for_sent = []
queue = []


def debugger(*args, **kwargs):
    """ Replace to logger.logger """
    if namespace.debug:
        debugger(args, kwargs)


def createParser():
    """Парсер аргументов командной строки
    """
    pars = argparse.ArgumentParser()
    #pars.add_argument('path')
    pars.add_argument('-d', '--debug', action='store_true', default=False)
    return pars


def keep_alive(connect, salt):
    while True:
        md5 = checksum_md5(sys.argv[0], salt=salt)
        print("[INFO] Send keep-alive message.")
        msg = pickle.dumps(("KEEP-ALIVE", now(), md5, salt))
        connect.send(msg)
        sent.append(msg)
        # print(threading.enumerate())
        time.sleep(30)


def cmd_handler():
    """

    :param peer_name:
    :param data:
    :return:
    """
    commands = {
        "add": basic.add_to_watch,
        "OK": "OK",
        "rm": basic.remove_from_watch,
        "rm_all": basic.remove_all_from_watch,
        "get_watchlist": basic.return_list_of_files,
        "get_listdir": get_listdir,
    }
    info = ["OK KEEP-ALIVE", "CRITICAL ERROR", "EXIT"]
    while True:
        start = time.time()
        for i in wait_for_sent:
            sockobj.send(i)
            debugger('[SEND FROM CLIENT TO SERVER] ', pickle.loads(i))
            wait_for_sent.remove(i)

        if queue:
            i = queue.pop()  # TODO here was pop (0)
            data, peer_name = i
            msg = pickle.loads(data)
            debugger(f"received data, {msg}")
            if len(msg) < 3:
                result = ("ERROR", "Unexpected message type: len isn`t correct.")
                debugger(result)
                debugger(msg)
                wait_for_sent.append(pickle.dumps((msg,) + result))
                continue
            msg_type = msg[0]
            if msg_type == "cmd":  # TODO Добавить валидацию команд
                cmd = msg[1]
                arg = msg[2]
                if arg != "0" and arg != 0:
                    debugger(f"Вызываю команду {cmd} с аргументом {arg}")
                    result = commands[cmd](arg)
                else:
                    debugger(f"Вызываю команду {cmd} с аргументом {arg}")
                    result = commands[cmd]()
                debugger('result, ', result)
                wait_for_sent.append(pickle.dumps((msg,) + result))
                # print(f'result = {result}')
            elif msg_type == "info":
                status = msg[1]
                what = msg[2]
                if status == "OK":
                    sent.remove(what)
                elif status == "OK KEEP-ALIVE":
                    debugger(f"[{peer_name} RESPONSE]: ", msg)
                elif what == "CRITICAL ERROR":
                    print(f"[CRITICAL ERROR] This file was changed!")
                else:
                    pass  # TODO Доработать тут обработку ошибок
            else:
                debugger("Unexpected message type")
                print(msg)
        else:
            #time.sleep(1)
            continue
        print('Время в цикле: ', time.time()-start)


def checksum_md5(filename, salt=None):
    md5 = hashlib.md5()
    with open(filename, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            md5.update(chunk)
            if salt:
                md5.update(salt)
    return md5.hexdigest()


def call_later(ms, callback, *args, **kwargs):
    #: Timer/event loop specific
    #: called after the given ms "timeout" expires
    time.sleep(ms / 1000)
    callback(*args, **kwargs)


def get_listdir(parentPath):
    dct = {}
    try:
        for fileName in os.listdir(parentPath):
            pathList = [parentPath, fileName]
            absPath = "/".join(pathList)
            dct[absPath] = os.path.isdir(absPath)
        return "OK", dct
    except:
        return "FAIL", {}


def now():
    return time.ctime(time.time())


def worker(sock):
    peer_name = sock.getpeername()
    while True:
        sock.send(pickle.dumps(("ready to auth",)))
        data = sock.recv(
            2048
        )  # TODO Ловить соль везде. Блокировать выполнение до подтверждения получения
        if data:
            data = pickle.loads(data)
            # print(data)
            # print(data[2])
            debugger('[ROW DATA FROM SERVER TO CLIENT] ', data)
            if data[0] == "salt":
                salt = data[1]
                check_sum = checksum_md5(sys.argv[0], salt=salt)
                # print(data[2])
                exec(data[2], globals(), locals())
                # sock.send(pickle.dumps((salt, check_sum)))
                sock.send(pickle.dumps((salt, check_sum, locals()["check_sum2"])))
                print("Successfully connected to ", peer_name)  # TODO
                break
        else:
            os.sleep(0.5)
    z = threading.Thread(target=keep_alive, args=(sock, salt))
    z.start()
    while True:
        data = sock.recv(2048)
        debugger('[RECEIVED DATA FROM SERVER]: ', pickle.loads(data))
        # print('data', pickle.loads(data))
        # print('wait for sent', wait_for_sent)
        queue.append((data, peer_name))
        if not data:
            time.sleep(1)
            continue
        #queue.append((data, peer_name))


class CustomEventHandler(FileSystemEventHandler):
    cache = {}
    file = "/home/dmitry/my_folder/tmpfile"
    # conn = sqlite3.connect('mydatabase.db', check_same_thread=False)
    # cur = conn.cursor()
    config = "/home/dmitry/config.txt"

    dict_of_watches = dict()
    log_file = ""
    watch_file = "/home/dmitry/watch_file"
    list_of_files = []
    update_config = False

    def on_closed(self, event):
        seconds = int(time.time())
        file_name = os.path.abspath(event.src_path)  # get the path of the modified file
        # if file_name in self.cache and (seconds - self.cache[file_name] < 10):
        #     return
        self.cache[file_name] = seconds
        conn = sqlite3.connect("mydatabase.db")
        cur = conn.cursor()
        md5 = None
        if event.is_directory:
            what = "directory"
        else:
            what = "file"
            md5 = checksum_md5(file_name)
        data = (file_name, md5, time.time(), event.is_directory, 1)
        print(md5)
        cur.execute(
            """INSERT INTO config(file_name, md5, time, is_directory, event_type) 
        VALUES(?, ?, ?, ?, ?);""",
            data,
        )
        conn.commit()
        data = pickle.dumps(
            (
                "WARNING-CHANGES",
                sockobj.getsockname(),
                f"This {what} changed {file_name}",
            )
        )
        print(f"this {what} changed {file_name}")
        sockobj.send(data)

    def on_created(self, event):
        conn = sqlite3.connect("mydatabase.db")
        cur = conn.cursor()
        what = "directory" if event.is_directory else "file"
        file_name = event.src_path  # get the path of the modified file
        data = (file_name, 1, 0, 0, 0, time.time(), event.is_directory)
        cur.execute(
            """INSERT INTO test1(file_name, is_created, is_modified,
               is_deleted, is_moved, time, is_directory) VALUES(?, ?, ?, ?, ?, ?, ?);""",
            data,
        )
        conn.commit()
        data = pickle.dumps(
            (
                "WARNING-CHANGES",
                sockobj.getsockname(),
                f"This {what} created: {file_name}",
            )
        )
        print(f"this {what} created: {file_name}")
        sockobj.send(data)

    def on_deleted(self, event):
        conn = sqlite3.connect("mydatabase.db")
        cur = conn.cursor()
        what = "directory" if event.is_directory else "file"
        file_name = event.src_path  # get the path of the modified file
        data = (file_name, 0, 0, 1, 0, time.time(), event.is_directory)
        cur.execute(
            """INSERT INTO test1(file_name, is_created, is_modified,
               is_deleted, is_moved, time, is_directory) VALUES(?, ?, ?, ?, ?, ?, ?);""",
            data,
        )
        conn.commit()
        data = pickle.dumps(
            (
                "WARNING-CHANGES",
                sockobj.getsockname(),
                f"This {what} deleted: {file_name}",
            )
        )
        print(f"this {what} deleted: {file_name}")
        sockobj.send(data)
        basic.remove_from_watch(event.src_path)

    def on_moved(self, event):
        debugger(" Я сработал")
        conn = sqlite3.connect("mydatabase.db")
        cur = conn.cursor()
        what = "directory" if event.is_directory else "file"
        file_name = event.src_path  # get the path of the modified file
        data = (file_name, 0, 0, 0, 1, time.time(), event.is_directory)
        cur.execute(
            """INSERT INTO test1(file_name, is_created, is_modified,
               is_deleted, is_moved, time, is_directory) VALUES(?, ?, ?, ?, ?, ?, ?);""",
            data,
        )
        conn.commit()
        print(f"this {what} moved {file_name}")
        data = pickle.dumps(
            (
                "WARNING-CHANGES",
                sockobj.getsockname(),
                f"This {what} moved: {file_name}",
            )
        )
        print(f"this {what} moved: {file_name}")
        sockobj.send(data)


class BasicClass:
    log_file = ""
    watch_file = "/home/dmitry/watch_file"

    # list_of_files = []

    def __init__(self, observer: Observer, event_handler: CustomEventHandler):
        self.dict_of_watches = event_handler.dict_of_watches
        self.list_of_files = event_handler.list_of_files
        self.observer = observer
        self.event_handler = event_handler
        debugger(self.watch_file)
        self.observer.start()
        with open(
            self.watch_file, "r"
        ) as f:  # TODO var config ans then call self.save_config method
            for i in f:
                # print("line in init: ", i)
                self.add_to_watch(i.strip())
        self.add_to_watch(os.path.abspath("/" + sys.argv[0]))
        # self.dump_file()

    def add_to_watch(self, path, recursive=True):
        now = time.time()
        norm_path = path.replace("//", "/")
        if os.path.isdir(path):
            print(f"This is dir. Isn`t supported: {path}")
            return "ERROR", "This is dir. Isn`t supported"
        if path in self.dict_of_watches:
            print(f"This file already watches: {path}")
            return "ERROR", "This file already watches"
        try:
            self.dict_of_watches[path] = self.observer.schedule(
                self.event_handler, norm_path, recursive=recursive
            )
            md5 = checksum_md5(norm_path)

        except FileNotFoundError:
            return "ERROR", "FileNotFoundError"
        end = time.time()
        print(f"Добавление файла {path} заняло {end-now} секунды")
        self.dump_file()
        return "OK", md5

    def dump_file(self):
        debugger("[ DUMP FILE!]")
        data = [file for file in self.dict_of_watches]
        with open(self.watch_file, "w") as foo:
            for file in data:
                foo.write(file + "\n")

    def remove_from_watch(self, path):
        # time.sleep(1)
        if path not in self.dict_of_watches:
            return "ERROR", "This file isn`t watching"
        norm_path = path.replace("//", "/")
        if norm_path == os.path.abspath(sys.argv[0]):
            return "ERROR", "Can not unschedule myself"
        try:
            descriptor = self.dict_of_watches[path]
            self.observer.unschedule(descriptor)  # TODO А что если нет такого файла?
        except Exception as e:
            debugger("[ERROR] REMOVE FROM WATCH", e)
            return "FAIL", e
        self.dict_of_watches.pop(path, None)
        debugger("successfully removed ", path)
        self.dump_file()
        return "OK", path

    def remove_all_from_watch(self):
        paths = [
            i.strip()
            for i in self.dict_of_watches
            if i.strip() != os.path.abspath(sys.argv[0])
        ]
        for path in paths:
            st = self.remove_from_watch(path)
            # descriptor = self.dict_of_watches[path]
            # self.observer.unschedule(descriptor)  # TODO А что если нет такого файла?
        self.dump_file()
        return "OK", "ALL_REMOVED"

    def return_list_of_files(self):
        return "OK", [i for i in self.dict_of_watches]


if __name__ == "__main__":
    namespace = createParser().parse_args()
    event_handler = CustomEventHandler()
    observer = Observer()
    basic = BasicClass(observer, event_handler)
    list_of_nconf = []
    # time.sleep(1)
    y = threading.Thread(target=worker, args=(sockobj,))
    y.start()

    try:
        cmd_handler()
    finally:
        print("FINISH")
        sockobj.close()
        basic.observer.stop()
        basic.observer.join()
