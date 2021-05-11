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

serverHost = '192.168.192.131'
serverPort = 50007
sockobj = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sockobj.connect((serverHost, serverPort))

sent = []
wait_for_sent = []


def keep_alive(connect, salt):
    while True:
        md5 = checksum_md5(sys.argv[0], salt=salt)
        print('[INFO] Send keep-alive message.')
        msg = pickle.dumps(('KEEP-ALIVE', now(), md5, salt))
        connect.send(msg)
        sent.append(msg)
        time.sleep(10)


def cmd_handler(data):
    """

    :param data:
    :return:
    """
    commands = {'add': basic.add_to_watch, 'OK': 'OK',
                'rm': basic.remove_from_watch, 'rm_all': basic.remove_all_from_watch,
                'send_cur_watches': basic.return_list_of_files,
                }
    info = ['OK KEEP-ALIVE', 'CRITICAL ERROR', 'EXIT']
    msg = pickle.loads(data)
    msg_type = msg[0]
    if msg_type == 'cmd':  # TODO Добавить валидацию команд
        cmd = msg[1]
        arg = msg[2]
        if arg != '0':
            result = commands[cmd](arg)
        else:
            result = commands[cmd]()
        wait_for_sent.append(pickle.dumps((msg,) + result))
    elif msg_type == 'info':
        status = msg[1]
        what = msg[2]
        if status == 'OK':
            sent.remove(what)
        elif status == 'OK KEEP-ALIVE':
            print(msg)
        else:
            pass  # TODO Доработать тут обработку ошибок
    else:
        print('Unexpected message type')
        print(msg)


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
        sock.send(pickle.dumps(('ready', sock.getpeername())))
        data = sock.recv(2048)  # TODO Ловить соль везде. Блокировать выполнение до подтверждения получения
        if data:
            salt = pickle.loads(data)
            if salt[0] == 'salt':
                salt = salt[1]
                sock.send(pickle.dumps(salt))
                print('success')
                break
    z = threading.Thread(target=keep_alive, args=(sock, salt))
    z.start()
    while True:
        data = sock.recv(1024)
        if not data:
            break
        cmd_handler(data)
        try:
            sock.send(wait_for_sent.pop())
        except IndexError:
            print('NOTHING TO SEND')
            continue


class CustomEventHandler(FileSystemEventHandler):
    cache = {}
    file = '/home/midway/my_folder/tmpfile'
    #conn = sqlite3.connect('mydatabase.db', check_same_thread=False)
    #cur = conn.cursor()
    config = '/home/midway/config.txt'

    dict_of_watches = dict()
    log_file = ''
    watch_file = '/home/midway/watch_file'
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
    watch_file = '/home/midway/watch_file'
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
            return 'ERROR', 'This file already watches'
        try:
            self.dict_of_watches[path] = self.observer.schedule(self.event_handler, path, recursive=recursive)
        except FileNotFoundError:
            return 'ERROR', 'FileNotFoundError'
        if self.clear_start:  # TODO Что это?
            pass
        self.list_of_files.append(os.path.abspath(path))
        self.dump_file()
        return 'OK', path

    def dump_file(self):
        print('dump_file was called')
        data = [file + '\n' for file in self.dict_of_watches]
        with open(self.watch_file, 'w') as foo:
            foo.writelines(data)

    def remove_from_watch(self, path):
        if path not in self.dict_of_watches:
            return 'ERROR', 'This file isn`t watching'
        descriptor = self.dict_of_watches[path]
        self.observer.unschedule(descriptor)  # TODO А что если нет такого файла?
        self.dict_of_watches.pop(path, None)
        return 'OK', path

    def remove_all_from_watch(self):
        self.observer.unschedule_all()
        self.dict_of_watches = {}
        return 'OK', 'ALL_REMOVED'

    def return_list_of_files(self):
        return 'OK', [i for i in self.dict_of_watches]

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