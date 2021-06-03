import os
import tkinter as tk
from ttkwidgets import CheckboxTreeview
import tkinter.ttk as ttk


def valid_ipv4(ip):
    lst = ip.split('.')
    if len(lst) != 4:
        return False
    for i in lst:
        if int(i) > 255 or int(i) < 0:
            return False
    return True


class CheckBoxTreeview(CheckboxTreeview):
    def __init__(self, master=None, **kw):
        CheckboxTreeview.__init__(self, master, **kw)
        # disabled tag to mar disabled items
        self.tag_configure("disabled", foreground='grey')
        self.tag_configure("ghost", foreground='#118515', font=('Arial', 12))

    def _box_click(self, event):
        """Check or uncheck box when clicked."""
        x, y, widget = event.x, event.y, event.widget
        elem = widget.identify("element", x, y)
        if "image" in elem:
            # a box was clicked
            item = self.identify_row(y)
            if self.tag_has("disabled", item) or self.tag_has('ghost', item):
                return  # do nothing when disabled
            if self.tag_has("unchecked", item) or self.tag_has("tristate", item):
                self._check_ancestor(item)
                self._check_descendant(item)
            elif self.tag_has("checked"):
                self._uncheck_descendant(item)
                self._uncheck_ancestor(item)


class App(object):
    def __init__(self, master, path):
        self.ghost = '127.0.0.1'
        self.dirs = {}
        self.nodes = dict()
        self.node = dict()
        self.parent_nodes = {}
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
        # frame.pack(side=tk.TOP, expand=tk.YES, fill=tk.BOTH)
        frame.grid(sticky=tk.NSEW)
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(0, weight=1)
        # style = ttk.Style()
        # style.configure('Checkbox.Treeview', rowheight=24)
        self.tree = CheckBoxTreeview(frame)
        # self.tree = ttk.Treeview(frame)
        self.tree["columns"] = ('#1', '#2', '#3')
        self.tree.column("#0", minwidth=150, width=300)
        self.tree.column("#1", minwidth=130, width=180)
        self.tree.column("#2", minwidth=180, width=250)
        self.tree.column("#3", minwidth=130, width=180)
        # self.tree.pack(side=tk.TOP, expand=tk.YES, fill=tk.BOTH)
        ysb = ttk.Scrollbar(frame, orient='vertical', command=self.tree.yview)
        xsb = ttk.Scrollbar(frame, orient='horizontal', command=self.tree.xview)
        self.tree.configure(yscroll=ysb.set, xscroll=xsb.set)
        self.tree.heading('#0', text='Узлы')
        self.tree.heading('#1', text="Статус соединения", anchor=tk.W)
        self.tree.heading('#2', text="Состояние защиты", anchor=tk.W)
        self.tree.heading('#3', text="Статус отслеживания", anchor=tk.W)
        self.tree.grid(sticky=tk.NSEW, rowspan=3)
        ysb.grid(row=0, column=1, sticky='ns', rowspan=3)
        xsb.grid(row=3, column=0, sticky='ew')
        self.button_add()
        self.button_lock()
        #self.btn_lock.deselect()
        self.var.set('Locked')

        # ysb.pack(side=tk.LEFT)
        # xsb.pack(side=tk.TOP)
        # frame.grid()
        # self.tree.pack(side=tk.LEFT, fill=tk.Y)
        abspath = '/'
        # node = self.tree.insert('', 'end', text='ghost1', open=False)
        # nt = self.tree.insert('', 'end', text='ghost2', open=False)
        # self.insert_node(node, abspath, abspath, client)
        self.tree.bind('<<TreeviewOpen>>', self.open_node)
        # self.tree.bind('')

    def insert_node(self, parent, text, abspath, client):
        self.call_client = client
        print(f'abspath {abspath} client {client}')
        node = self.tree.insert(parent, 'end', text=text, open=False)
        self.tree.tag_add(node, client)
        if self.var.get() == 'Locked':
            self.tree.tag_add(node, 'disabled')
        print(self.tree.item(node))
        print('node', node)
        self.node[client][node] = abspath
        if abspath in self.dirs[client]:
            self.nodes[client][node] = abspath
            self.tree.insert(node, 'end')

    def open_node(self, event):
        print(f'[open node] call_client, {self.call_client}')
        node = self.tree.focus()
        print('[open node] focus_node', node)
        print(self.nodes)
        abspath = self.nodes[self.call_client].pop(node, None)
        print('abspath poped', abspath)
        if abspath:
            self.tree.delete(self.tree.get_children(node))
            for p in self.listdir(abspath, self.call_client):
                self.insert_node(node, os.path.split(p)[1], p, self.call_client)

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
                # client_ip = max(map(lambda x: len(x.split('.')), tags))
                # client_ip, *_ = tags
                client_ip = None
                for tag in tags:
                    if valid_ipv4(tag):
                        client_ip = tag

                if not client_ip:
                    continue
                path = self.node[client_ip][i]

                if client_ip not in selected:
                    selected[client_ip] = [path]
                else:
                    selected[client_ip].append(path)
            except KeyError:
                pass
        return selected

    def button_add(self):
        self.button = tk.Button(self.frame)
        self.button.config(text='add', command=self.send_checked, width=8, height=1)
        self.button.grid(row=5, column=0, sticky='w')

    def button_lock(self):
        self.var = tk.StringVar()
        self.btn_lock = tk.Checkbutton(self.frame)
        self.btn_lock.config(onvalue='Unlocked', offvalue='Locked', indicatoron=False, variable=self.var,
                             width=8, height=1,
                             textvariable=self.var,
                             command=self.toggle
                             )
        self.btn_lock.grid(row=5, column=0, sticky='e')

    def toggle(self):  # TODO dict with variables (self.vars = dict())
        if self.var.get() == "ON":
            print("turning on...")
        else:
            print("turning off...")

    def send_checked(self):
        pass

# if __name__ == '__main__':
#     root = tk.Tk()
#     app = App(root, path='.')
#     root.mainloop()
