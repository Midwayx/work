#!/home/dmitry/Projects/checker/env/bin/python
# -*- coding: utf-8 -*-


import argparse # kill server, restart server, start graphsesion
import os
import signal
import subprocess

SCRIPTNAME = 'server.py'

run = subprocess.Popen(["ps", "axf"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

output, errors = run.communicate()
#print(output, errors)
list_pid = list()
if not errors:
    list_pid = [i for i in output.strip().split('\n') if SCRIPTNAME in i]
else:
    print(f'{errors}')
if len(list_pid) == 0:
    print(f'Невозможно запустить графическую среду.\nНе запущен сервер!')
elif len(list_pid) > 1:
    print('Ошибка! Невозможно запустить скрипт!\nВозможно, запущено более 1го экземпляра сервера.')
else:
    pid = int(list_pid[0].split()[0])
    os.kill(pid, signal.SIGUSR1)
    #print(pid)