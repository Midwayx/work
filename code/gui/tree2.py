import os
import tkinter as tk
from ttkwidgets import CheckboxTreeview
import tkinter.ttk as ttk


class App(object):
    def __init__(self, master, path):
        self.ghost = '127.0.0.1'
        self.dirs = {}
        self.nodes = dict()
        self.node = dict()
        self.master = master
        master.grid_columnconfigure(0, weight=1)
        master.grid_rowconfigure(0, weight=1)
        # for x in range(60):
        #     tk.Grid.columnconfigure(grid, x, weight=1)
        #
        # for y in range(30):
        #     tk.Grid.rowconfigure(grid, y, weight=1)
        frame = tk.Frame(master)
        self.frame = frame
        #frame.pack(side=tk.TOP, expand=tk.YES, fill=tk.BOTH)
        frame.grid(sticky=tk.NSEW)
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(0, weight=1)

        self.tree = CheckboxTreeview(frame)
        #self.tree = ttk.Treeview(frame)
        self.tree["columns"] = ('#1', '#2', '#3')
        self.tree.column("#0", minwidth=150, width=200)
        self.tree.column("#1", minwidth=150, width=200)
        self.tree.column("#2", minwidth=150, width=200)
        self.tree.column("#3", minwidth=150, width=200)
        #self.tree.pack(side=tk.TOP, expand=tk.YES, fill=tk.BOTH)
        ysb = ttk.Scrollbar(frame, orient='vertical', command=self.tree.yview)
        xsb = ttk.Scrollbar(frame, orient='horizontal', command=self.tree.xview)
        self.tree.configure(yscroll=ysb.set, xscroll=xsb.set)
        self.tree.heading('#0', text='Project tree')
        self.tree.heading('#1', text="Date modified", anchor=tk.W)
        self.tree.heading('#2', text="Type", anchor=tk.W)
        self.tree.heading('#3', text="Size", anchor=tk.W)
        self.tree.grid(sticky=tk.NSEW, rowspan=3)
        ysb.grid(row=0, column=1, sticky='ns', rowspan=3)
        xsb.grid(row=3, column=0, sticky='ew')
        self.button_1()

        # ysb.pack(side=tk.LEFT)
        # xsb.pack(side=tk.TOP)
        # frame.grid()
        #self.tree.pack(side=tk.LEFT, fill=tk.Y)
        abspath = '/'
        # node = self.tree.insert('', 'end', text='ghost1', open=False)
        # nt = self.tree.insert('', 'end', text='ghost2', open=False)
        #self.insert_node(node, abspath, abspath, client)
        self.tree.bind('<<TreeviewOpen>>', self.open_node)

    def insert_node(self, parent, text, abspath, client):
        self.call_client = client
        print(f'abspath {abspath} client {client}')
        node = self.tree.insert(parent, 'end', text=text, open=False)
        self.tree.tag_add(node, client)
        print('node', node)
        self.node[client][node] = abspath
        if abspath in self.dirs[client]:
            self.nodes[client][node] = abspath
            self.tree.insert(node, 'end')

    def open_node(self, event):
        print(f'open node, {self.call_client}')
        node = self.tree.focus()
        print('open nodes', node)
        print(self.nodes)
        abspath = self.nodes[self.call_client].pop(node, None)
        print('abspath poped', abspath)
        if abspath:
            self.tree.delete(self.tree.get_children(node))
            for p in self.listdir(abspath, self.call_client):
                self.insert_node(node, os.path.split(p)[1], p, self.call_client)
        #print('get checked', self.get_checked())

    def listdir(self, abspath, host=None):
        return "MOCK"

    def is_dir(self, abspath):
        pass

    def get_checked(self):
        s = self.tree.get_checked()
        selected = {}
        print(f'self.tree.get-checked() = {s}')
        for i in s:
            try:
                print(self.tree.item(i))
                tags = self.tree.item(i)['tags']  # TODO validation ip

                #client_ip = max(map(lambda x: len(x.split('.')), tags))
                client_ip, *_ = tags
                if not _:
                    continue
                path = self.node[client_ip][i]

                if client_ip not in selected:
                    selected[client_ip] = [path]
                else:
                    selected[client_ip].append(path)
            except KeyError:
                pass
        return selected

    def button_1(self):
        self.button = ttk.Button(self.frame)
        self.button.config(text='add', command=self.send_checked)
        self.button.grid(row=5, column=0, sticky='w')

    def send_checked(self):
        pass




# if __name__ == '__main__':
#     root = tk.Tk()
#     app = App(root, path='.')
#     root.mainloop()