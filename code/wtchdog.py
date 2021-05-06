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

serverHost = 'localhost'
serverPort = 50007
sockobj = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sockobj.connect((serverHost, serverPort))


def keep_alive(connect, salt):
    # while True:
    #     salt = connect.recv(2048)  # TODO Ловить соль везде. Блокировать выполнение до подтверждения получения
    #     if salt:
    #         salt = pickle.loads(salt)
    #         if salt[0] == 'salt':
    #             salt = salt[1]
    #             break

    while True:
        # md5 = checksum_md5(sys.argv[0], salt=salt)
        # print('[INFO] Send keep-alive message.')
        # msg = pickle.dumps(('KEEP-ALIVE', now(), md5, salt))
        # connect.send(msg)
        # #ans = connect.recv(1024)
        # #print(pickle.loads(ans))
        # #changes
        time.sleep(10)


def checksum_md5(filename, salt=None):
    md5 = hashlib.md5()
    with open(filename, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            md5.update(chunk)
            if salt:
                md5.update(salt)
    return md5.hexdigest()


def call_later(ms, callback, *args, **kwargs):
   #: Timer/event loop specific
   #: called after the given ms "timeout" expires
    time.sleep(ms/1000)
    callback(*args, **kwargs)


def now():
    return time.ctime(time.time())

def worker(sock):
    while True:
        salt = sock.recv(2048)  # TODO Ловить соль везде. Блокировать выполнение до подтверждения получения
        if salt:
            salt = pickle.loads(salt)
            if salt[0] == 'salt':
                salt = salt[1]
                break
    z = threading.Thread(target=keep_alive, args=(sock, salt))
    z.start()
    commands = {'add': basic.add_to_watch, 'OK': 'OK',
                'rm': basic.remove_from_watch, 'rm_all': basic.remove_all_from_watch,
                'send_cur_watches': basic.return_list_of_files,
                }
    info = ['OK KEEP-ALIVE', 'CRITICAL ERROR', 'EXIT']
    while True:
        data = sock.recv(1024)
        if not data:
            time.sleep(1)
            continue
        try:
            cmd = pickle.loads(data)
            #print(cmd)
            if cmd[0] in info:
                print(f'[INFO Requested from {sock.getpeername()}]', cmd)
                if cmd[0] == 'EXIT':
                    sys.exit()
                continue
            if cmd[0] in commands:  # TODO  адекватно переписать, чушь полная, обработчки в отдельную функцию
                print('COMMAND ')
                print(cmd)
                print(len(cmd))
                if len(cmd) == 2:
                    commands[cmd[0]](cmd[1])
                elif len(cmd) == 1:
                    if cmd[0] == 'send_cur_watches':
                        response = ('OK', ('send_cur_watches',), commands[cmd[0]]())
                        print(response)
                        ans = pickle.dumps(response)
                        sock.send(ans)
                        continue
                    commands[cmd[0]]()
            else:
                print('Unsupported command')
                print(pickle.loads(data))
                continue
            ans = pickle.dumps(('OK', cmd))
            sock.send(ans)  # TODO отправлять из другого места, так как тут не гарантируется успешность

        except Exception as e:
            print('except  ', e.args)
            continue


class CustomEventHandler(FileSystemEventHandler):
    cache = {}
    file = '/home/user/my_folder/tmpfile'
    #conn = sqlite3.connect('mydatabase.db', check_same_thread=False)
    #cur = conn.cursor()
    config = '/home/user/config.txt'

    dict_of_watches = dict()
    log_file = ''
    watch_file = '/home/user/watch_file'
    list_of_files = []
    update_config = False

    def on_closed(self, event):
        seconds = int(time.time())
        file_name = os.path.abspath(event.src_path) # get the path of the modified file
        if file_name in self.cache and (seconds - self.cache[file_name] < 10):
            #print(seconds - self.cache[file_name])
            return
        self.cache[file_name] = seconds
        conn = sqlite3.connect('mydatabase.db')
        cur = conn.cursor()
        md5 = None
        if event.is_directory:
            what = 'directory'
        else:
            what = 'file'
            md5 = checksum_md5(file_name)
        data = (file_name, md5, time.time(), event.is_directory, 1)
        print(md5)
        #if file_name == self.config:
         #   print('WOW!!!')
          #  self.update_config = True
           # print(self.update_config)

        cur.execute("""INSERT INTO config(file_name, md5, time, is_directory, event_type) 
        VALUES(?, ?, ?, ?, ?);""", data)
        conn.commit()
        data = pickle.dumps(('WARNING-CHANGES', sockobj.getsockname(), f'This {what} changed {file_name}'))
        print(f'this {what} changed {file_name}')
        sockobj.send(data)

    def on_created(self, event):
        conn = sqlite3.connect('mydatabase.db')
        cur = conn.cursor()
        what = 'directory' if event.is_directory else 'file'
        file_name = event.src_path  # get the path of the modified file
        data = (file_name, 1, 0, 0, 0, time.time(), event.is_directory)
        cur.execute("""INSERT INTO test1(file_name, is_created, is_modified,
               is_deleted, is_moved, time, is_directory) VALUES(?, ?, ?, ?, ?, ?, ?);""", data)
        conn.commit()
        print(f'this {what} created {file_name}')
        # print([i for i in self.dict_of_watches])
        # with open(self.file, 'a') as f:
        #     f.writelines('this {} created {}\n'.format(what, os.path.abspath(file_name)))

    def on_deleted(self, event):
        conn = sqlite3.connect('mydatabase.db')
        cur = conn.cursor()
        what = 'directory' if event.is_directory else 'file'
        file_name = event.src_path  # get the path of the modified file
        data = (file_name, 0, 0, 1, 0, time.time(), event.is_directory)
        cur.execute("""INSERT INTO test1(file_name, is_created, is_modified,
               is_deleted, is_moved, time, is_directory) VALUES(?, ?, ?, ?, ?, ?, ?);""", data)
        conn.commit()
        print(f'this {what} deleted {file_name}')
        # print([i for i in self.dict_of_watches])
        # with open(self.file, 'a') as f:
        #     f.writelines('this {} deleted {}\n'.format(what, os.path.abspath(file_name)))

    def on_moved(self, event):
        conn = sqlite3.connect('mydatabase.db')
        cur = conn.cursor()
        what = 'directory' if event.is_directory else 'file'
        file_name = event.src_path  # get the path of the modified file
        data = (file_name, 0, 0, 0, 1, time.time(), event.is_directory)
        cur.execute("""INSERT INTO test1(file_name, is_created, is_modified,
               is_deleted, is_moved, time, is_directory) VALUES(?, ?, ?, ?, ?, ?, ?);""", data)
        conn.commit()
        print(f'this {what} moved {file_name}')
        # print([i for i in self.dict_of_watches])
        # with open(self.file, 'a') as f:
        #     f.writelines('this {} moved {}\n'.format(what, os.path.abspath(file_name)))


class BasicClass:

    # dict_of_watches = event_handler.dict_of_watches
    log_file = ''
    watch_file = '/home/user/watch_file'
    # list_of_files = []

    def __init__(self, observer: Observer, event_handler: CustomEventHandler):
        self.dict_of_watches = event_handler.dict_of_watches
        self.list_of_files = event_handler.list_of_files
        self.observer = observer
        self.event_handler = event_handler
        self.clear_start = False
        print(self.watch_file)
        with open(self.watch_file, 'r') as f:
            for i in f:
                #print(i, 'Наполняем list-of_files из watch_file')  # debug
                self.list_of_files.append(i.strip())  # TODO Переписать красиво
            if self.list_of_files:
                for path in self.list_of_files:
                    #print(path, 'Пути из list_of_file')  # debug
                    self.add_to_watch(path)  # ФЛАГ рекурсии? получать конфиг из базы при пуске
                #self.dump_file()
                self.clear_start = False
                self.observer.start()
            else:
                self.dict_of_watches = dict()
                self.clear_start = True

    def add_to_watch(self, path, recursive=True):
        if path in self.dict_of_watches:
            print('This file already watches')
            return
        self.dict_of_watches[path] = self.observer.schedule(self.event_handler, path, recursive=recursive)
        if self.clear_start:  # TODO Что это?
            pass
        self.list_of_files.append(os.path.abspath(path))
        self.dump_file()

    def dump_file(self):
        print('dump_file was called')
        data = [file + '\n' for file in self.dict_of_watches]
        with open(self.watch_file, 'w') as foo:
            foo.writelines(data)

    def remove_from_watch(self, path):
        descriptor = self.dict_of_watches[path]
        self.observer.unschedule(descriptor)
        self.dict_of_watches.pop(path, None)
        #self.list_of_files.remove(path)

    def remove_all_from_watch(self):
        self.observer.unschedule_all()
        self.dict_of_watches = {}

    def return_list_of_files(self):
        return [i for i in self.dict_of_watches]


if __name__ == "__main__":
    event_handler = CustomEventHandler()
    observer = Observer()
    basic = BasicClass(observer, event_handler)
    list_of_nconf = []
    time.sleep(1)
    #x = threading.Thread(target=keep_alive, args=(sockobj,))
    #x.start()
    y = threading.Thread(target=worker, args=(sockobj,))
    y.start()

    try:
        while True:

            if basic.clear_start:
                path = input('Input path to file or directory\n')  # TODO Исправить/удалить
                basic.add_to_watch(path)
                basic.dump_file()
                basic.observer.start()
                basic.clear_start = False
            else:
                time.sleep(1)

    finally:
        print('FINISH')
        sockobj.close()
        basic.observer.stop()
        basic.observer.join()