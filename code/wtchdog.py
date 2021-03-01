import sys
import time
import logging
import os
from watchdog.observers import Observer
from watchdog.events import LoggingEventHandler, FileSystemEventHandler, FileSystemEvent
import sqlite3


class CustomEventHandler(FileSystemEventHandler):
    file = '/home/user/my_folder/tmpfile'
    #conn = sqlite3.connect('mydatabase.db', check_same_thread=False)
    #cur = conn.cursor()
    config = '/home/user/config.txt'

    dict_of_watches = dict()
    log_file = ''
    watch_file = '/home/user/watch_file'
    list_of_files = []
    update_config = False

    def on_modified(self, event):
        conn = sqlite3.connect('mydatabase.db')
        cur = conn.cursor()
        what = 'directory' if event.is_directory else 'file'
        file_name = os.path.abspath(event.src_path)  # get the path of the modified file
        data = (file_name, 0, 1, 0, 0, time.time(), event.is_directory)
        if file_name == self.config:
            print('WOW!!!!!')
            self.update_config = True

        cur.execute("""INSERT INTO test1(file_name, is_created, is_modified,
        is_deleted, is_moved, time, is_directory) VALUES(?, ?, ?, ?, ?, ?, ?);""", data)
        conn.commit()
        with open(self.file, 'a') as f:
            f.writelines('this {} changed {}\n'.format(what, file_name))

    def on_created(self, event):
        conn = sqlite3.connect('mydatabase.db')
        cur = conn.cursor()
        what = 'directory' if event.is_directory else 'file'
        file_name = event.src_path  # get the path of the modified file
        data = (file_name, 1, 0, 0, 0, time.time(), event.is_directory)
        cur.execute("""INSERT INTO test1(file_name, is_created, is_modified,
               is_deleted, is_moved, time, is_directory) VALUES(?, ?, ?, ?, ?, ?, ?);""", data)
        conn.commit()
        with open(self.file, 'a') as f:
            f.writelines('this {} created {}\n'.format(what, os.path.abspath(file_name)))

    def on_deleted(self, event):
        conn = sqlite3.connect('mydatabase.db')
        cur = conn.cursor()
        what = 'directory' if event.is_directory else 'file'
        file_name = event.src_path  # get the path of the modified file
        data = (file_name, 0, 0, 1, 0, time.time(), event.is_directory)
        cur.execute("""INSERT INTO test1(file_name, is_created, is_modified,
               is_deleted, is_moved, time, is_directory) VALUES(?, ?, ?, ?, ?, ?, ?);""", data)
        conn.commit()
        with open(self.file, 'a') as f:
            f.writelines('this {} deleted {}\n'.format(what, os.path.abspath(file_name)))

    def on_moved(self, event):
        conn = sqlite3.connect('mydatabase.db')
        cur = conn.cursor()
        what = 'directory' if event.is_directory else 'file'
        file_name = event.src_path  # get the path of the modified file
        data = (file_name, 0, 0, 0, 1, time.time(), event.is_directory)
        cur.execute("""INSERT INTO test1(file_name, is_created, is_modified,
               is_deleted, is_moved, time, is_directory) VALUES(?, ?, ?, ?, ?, ?, ?);""", data)
        conn.commit()
        with open(self.file, 'a') as f:
            f.writelines('this {} moved {}\n'.format(what, os.path.abspath(file_name)))


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
                print(i, 'Наполняем list-of_files из watch_file')  # debug
                self.list_of_files.append(i.strip())
            if self.list_of_files:
                for path in self.list_of_files:
                    print(path, 'Пути из list_of_file')  # debug
                    self.add_to_watch(path)  # ФЛАГ рекурсии?
                self.dump_file()
                self.clear_start = False
                self.observer.start()
            else:
                self.dict_of_watches = dict()
                self.clear_start = True

    def add_to_watch(self, path, recursive=True):
        self.dict_of_watches[path] = self.observer.schedule(self.event_handler, path, recursive=recursive)
        if self.clear_start:
            self.list_of_files.append(os.path.abspath(path))

    def dump_file(self):
        with open(self.watch_file, 'w') as f:
            f.writelines(self.list_of_files)

    def remove_from_watch(self, path):
        descriptor = self.dict_of_watches[path]
        self.observer.unschedule(descriptor)
        self.dict_of_watches.pop(path, None)
        self.list_of_files.remove(path)

    def remove_all_from_watch(self):
        self.observer.unschedule_all()


if __name__ == "__main__":
    event_handler = CustomEventHandler()
    observer = Observer()
    basic = BasicClass(observer, event_handler)
    list_of_nconf = []

    try:
        while True:
            if basic.clear_start:
                path = input('Input path to file or directory\n')
                basic.add_to_watch(path)
                basic.dump_file()
                basic.observer.start()
                basic.clear_start = False
            elif basic.event_handler.update_config:
                print('CHANGED STATUS')
                time.sleep(5)
                with open(basic.event_handler.config, 'r') as f:
                    for i in f:
                        list_of_nconf.append((i.strip().split()))

                print(list_of_nconf, 'list of new configs')
                for i, j in list_of_nconf:
                    if int(i) == 0:
                        if j in basic.dict_of_watches:
                            basic.remove_from_watch(j)
                            basic.dump_file()
                        else:
                            print('this file is not watching: ', j)
                    if int(i) == 1:
                        if j in basic.dict_of_watches:
                            print('This file already watching: ', j)
                        else:
                            basic.add_to_watch(j)
                            basic.dump_file()
                print('update_config: ', basic.event_handler.update_config)
                print('dict of files after update: \n', basic.dict_of_watches)
                time.sleep(3)
                print('спим 3 сек')
                basic.event_handler.update_config = False
            print('update_config: ', basic.event_handler.update_config)

                # new_command, path = input('Input command and path to file\n').split()
                # if new_command == 'add':
                #     basic.add_to_watch(path)
                #     basic.dump_file()
                #
                # if new_command == 'remove':
                #     if path in basic.dict_of_watches:
                #         basic.remove_from_watch(path)
                #         basic.dump_file()

    finally:
        basic.observer.stop()
        basic.observer.join()