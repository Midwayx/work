import os
import tkinter as tk
import tkinter.ttk as ttk


class App(object):
    def __init__(self, master, path):
        self.ghost = '127.0.0.1'
        self.dirs = ['/']
        self.nodes = dict()
        frame = tk.Frame(master)
        self.frame = frame
        frame.pack(side=tk.TOP, expand=tk.YES, fill=tk.BOTH)
        self.tree = ttk.Treeview(frame)
        self.tree["columns"] = ('#1', '#2', '#3')
        self.tree.pack(side=tk.TOP, fill=tk.BOTH, expand=tk.YES)
        # ysb = ttk.Scrollbar(frame, orient='vertical', command=self.tree.yview)
        # xsb = ttk.Scrollbar(frame, orient='horizontal', command=self.tree.xview)
        # self.tree.configure(yscroll=ysb.set, xscroll=xsb.set)
        self.sc = tk.Scrollbar(frame)
        self.sc.pack(side=tk.RIGHT, fill=tk.Y)
        self.sc.config(command=self.tree.yview)
        self.tree.config(yscrollcommand=self.sc.set)
        # self.scx = tk.Scrollbar(frame)
        # self.scx.pack(side=tk.BOTTOM, fill=tk.X)
        # self.scx.config(command=self.tree.xview)
        # self.tree.config(xscrollcommand=self.scx.set)
        self.tree.heading('#0', text='Project tree')
        self.tree.heading('#1', text="Date modified", anchor=tk.W)
        self.tree.heading('#2', text="Type", anchor=tk.W)
        self.tree.heading('#3', text="Size", anchor=tk.W)
        # self.tree.grid()
        # ysb.grid(row=0, column=1, sticky='ns')
        # xsb.grid(row=1, column=0, sticky='ew')
        # frame.grid()
        #self.tree.pack(side=tk.LEFT, fill=tk.Y)
        abspath = '/'
        node = self.tree.insert('', 'end', text='ghost1', open=False)
        nt = self.tree.insert('', 'end', text='ghost2', open=False)
        self.insert_node(node, abspath, abspath)
        self.tree.bind('<<TreeviewOpen>>', self.open_node)

    def insert_node(self, parent, text, abspath):
        print('abspath', abspath)
        node = self.tree.insert(parent, 'end', text=text, open=False)
        if abspath in self.dirs:
            self.nodes[node] = abspath
            self.tree.insert(node, 'end')

    def open_node(self, event):
        node = self.tree.focus()
        abspath = self.nodes.pop(node, None)
        if abspath:
            self.tree.delete(self.tree.get_children(node))
            for p in self.listdir(abspath):
                self.insert_node(node, os.path.split(p)[1], p)

    def listdir(self, abspath):
        pass

    def is_dir(self, abspath):
        pass


# if __name__ == '__main__':
#     root = tk.Tk()
#     app = App(root, path='.')
#     root.mainloop()