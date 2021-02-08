import inotify.adapters


def _main():
    i = inotify.adapters.Inotify()

    i.add_watch('/tmp/testfile.txt')

    with open('/tmp/test_file', 'w'):
        pass

    for event in i.event_gen(yield_nones=False):
        (header, type_names, path, filename) = event

        print(" HEADER [{}] PATH=[{}] FILENAME=[{}] EVENT_TYPES={}".format(header,
              path, filename, type_names))


if __name__ == '__main__':
    _main()
    print('Privet')
