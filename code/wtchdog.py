import sys
import time
import logging
import os
from watchdog.observers import Observer
from watchdog.events import LoggingEventHandler, FileSystemEventHandler, FileSystemEvent


class CustomEventHandler(FileSystemEventHandler):
    file = '/home/user/my_folder/tmpfile'

    # def __init__(self):
    #     self.fd_open = open('tmpfile.txt', 'w+')
    #     self.fd_close = self.fd_open.close()

    def on_modified(self, event):
        what = 'directory' if event.is_directory else 'file'
        file_name = event.src_path  # get the path of the modified file
        #print('this {} changed {}'.format(what, os.path.abspath(file_name)))
        # self.fd_open.writelines('this {} changed {}\n'.format(what, os.path.abspath(file_name)))
        # self.fd_close()
        with open(self.file, 'a') as f:
            f.writelines('this {} changed {}\n'.format(what, os.path.abspath(file_name)))


    def on_created(self, event):
        what = 'directory' if event.is_directory else 'file'
        file_name = event.src_path  # get the path of the modified file
        #print('this {} created {}'.format(what, os.path.abspath(file_name)))
        # self.fd_open.writelines('this {} created {}\n'.format(what, os.path.abspath(file_name)))
        # self.fd_close()
        with open(self.file, 'a') as f:
            f.writelines('this {} created {}\n'.format(what, os.path.abspath(file_name)))

    def on_deleted(self, event):
        what = 'directory' if event.is_directory else 'file'
        file_name = event.src_path  # get the path of the modified file
        #print('this {} deleted {}'.format(what, os.path.abspath(file_name)))
        # self.fd_open.writelines('this {} deleted {}\n'.format(what, os.path.abspath(file_name)))
        # self.fd_close()
        with open(self.file, 'a') as f:
            f.writelines('this {} deleted {}\n'.format(what, os.path.abspath(file_name)))

    def on_moved(self, event):
        what = 'directory' if event.is_directory else 'file'
        file_name = event.src_path  # get the path of the modified file
        #print('this {} moved {}'.format(what, os.path.abspath(file_name)))
        # self.fd_open.writelines('this {} moved {}\n'.format(what, os.path.abspath(file_name)))
        # self.fd_close()
        with open(self.file, 'a') as f:
            f.writelines('this {} moved {}\n'.format(what, os.path.abspath(file_name)))


class BasicClass:

    dict_of_watches = dict()
    log_file = ''
    watch_file = '/home/user/watch_file'
    list_of_files = []

    def __init__(self, observer: Observer, event_handler: CustomEventHandler):
        self.observer = observer
        self.event_handler = event_handler
        self.clear_start = False
        print(self.watch_file)
        with open(self.watch_file, 'r') as f:
            for i in f:
                print(i)
                self.list_of_files.append(i.strip())
            if self.list_of_files:
                print(self.list_of_files)
                for path in self.list_of_files:
                    print(path)
                    self.add_to_watch(path) # ФЛАГ рекурсии?
                self.dump_file()
                self.clear_start = False
                self.observer.start()

            else:
                self.dict_of_watches = dict()
                self.clear_start = True

    def add_to_watch(self, path, recursive=True):
        #print('h')
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
    # dict_of_watches = {}
    # logging.basicConfig(level=logging.INFO,
    #                     format='%(asctime)s - %(message)s',
    #                     datefmt='%Y-%m-%d %H:%M:%S')
    # path = sys.argv[1] if len(sys.argv) > 1 else '.'
    # #event_handler = LoggingEventHandler()
    event_handler = CustomEventHandler()

    observer = Observer()
    #observer.daemon = True
    basic = BasicClass(observer, event_handler)
    # dict_of_watches[path] = observer.schedule(event_handler, path, recursive=True)
    # observer.start()
    try:
        while True:
            #time.sleep(1)
            if basic.clear_start:
                path = input('Input path to file or directory\n')
                basic.add_to_watch(path)
                basic.dump_file()
                basic.observer.start()
                basic.clear_start = False
            else:
                #basic.observer.start()
                new_command, path = input('Input command and path to file\n').split()
                if new_command == 'add':
                    basic.add_to_watch(path)
                    basic.dump_file()
                    # with open('/home/user/file_list', 'w') as f:
                    #     f.write(str(dict_of_watches))

                if new_command == 'remove':
                    if path in basic.dict_of_watches:
                        basic.remove_from_watch(path)
                        basic.dump_file()
                        # dict_of_watches.pop(path, None)
                        # with open('/home/user/file_list', 'w') as f:
                        #     f.write(str(dict_of_watches))

    finally:
        basic.observer.stop()
        basic.observer.join()