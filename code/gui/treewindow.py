import tkinter
from tkinter import ttk
import os


class TreeWindow(tkinter.Frame):
    def __init__(self, master, path, otherWin):
        self.otherWin = otherWin

        frame = tkinter.Frame(master)
        frame.grid(row=0, column=0)

        # Создать фрейм
        self.tree = ttk.Treeview(frame)
        self.tree.pack(side=tkinter.LEFT, fill=tkinter.Y)
        # Загружаем корневой каталог
        curPath = self.getLastPaht(path)
        root = self.tree.insert("", "end", text=curPath, open=True, values=(path))
        # Загрузить подкаталог
        self.loadTree(root, path)
        # Добавить полосу прокрутки
        self.sc = tkinter.Scrollbar(frame)
        self.sc.pack(side=tkinter.RIGHT, fill=tkinter.Y)
        self.sc.config(command=self.tree.yview)
        self.tree.config(yscrollcommand=self.sc.set)

        # Связывающее событие
        self.tree.bind("<<TreeviewSelect>>", self.func)

    def func(self, event):
        self.v = event.widget.selection()
        for sv in self.v:
            file = self.tree.item(sv)["text"]
            self.otherWin.var.set(file)
            absPath = self.tree.item(sv)["values"][0]
            print(absPath)
            if self.file_extension(absPath) == ".py":
                with open(absPath, "r", encoding="utf-8") as f:
                    self.otherWin.txt.insert(tkinter.INSERT, f.read())

        # Получить расширение файла

    def file_extension(self, filePath):
        return os.path.splitext(filePath)[1]

    def loadTree(self, parent, parentPath):
        for fileName in os.listdir(parentPath):
            pathList = [parentPath, fileName]
            absPath = "/".join(pathList)
            # Вставить ветку первого уровня
            treep = self.tree.insert(
                parent, "end", text=self.getLastPaht(absPath), values=(absPath)
            )
            # Определить, является ли это каталогом
            if os.path.isdir(absPath):
                self.loadTree(treep, absPath)

        # Получить каталог последнего уровня для отображения

    def getLastPaht(self, path):
        pathList = os.path.split(path)
        return pathList[-1]


class InfoWindow(tkinter.Frame):
    def __init__(self, master):
        frame = tkinter.Frame(master)
        frame.grid(row=0, column=1)

        self.var = tkinter.Variable()
        self.entry = tkinter.Entry(frame, textvariable=self.var)
        self.entry.pack()

        self.txt = tkinter.Text(frame)
        self.txt.pack()
