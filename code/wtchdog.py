import sys
import time
import logging
import os
from watchdog.observers import Observer
from watchdog.events import LoggingEventHandler, FileSystemEventHandler, FileSystemEvent


class CustomEventHandler(FileSystemEventHandler):

    def on_modified(self, event):

        what = 'directory' if event.is_directory else 'file'
        file_name = event.src_path  # get the path of the modified file
        print('this {} changed {}'.format(what, os.path.abspath(file_name)))


if __name__ == "__main__":
    dict_of_watches = {}
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')
    path = sys.argv[1] if len(sys.argv) > 1 else '.'
    #event_handler = LoggingEventHandler()
    event_handler = CustomEventHandler()

    observer = Observer()
    observer.daemon = True
    dict_of_watches[path] = observer.schedule(event_handler, path, recursive=True)
    observer.start()
    try:
        while True:
            #time.sleep(1)
            new_command, path = input('Command\n').split()
            if new_command == 'add':
                dict_of_watches[path] = observer.schedule(event_handler, path)
            if new_command == 'remove':
                if path in dict_of_watches:
                    observer.unschedule(dict_of_watches[path])
    finally:
        observer.stop()
        observer.join()