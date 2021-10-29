import os
import tkinter as tk
from ttkwidgets import CheckboxTreeview
import tkinter.ttk as ttk


def valid_ipv4(ip):
    lst = ip.split(".")
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
        self.tag_configure("changed", foreground='black', background='#FF8000')
        self.tag_configure("disabled", foreground="grey")
        self.tag_configure("ghost", foreground="#118515")
        self.tag_configure("disconnected", foreground="red")
        self.tag_configure("odd", background="grey")
        self.tag_configure('to_remove', background="yellow")
        self.tag_configure('to_add', background="yellow")
        self.tag_configure('highlight', background="lightblue")
        self.saved_node = []

    def _box_click(self, event):
        """Check or uncheck box when clicked."""
        x, y, widget = event.x, event.y, event.widget
        elem = widget.identify("element", x, y)
        if "image" in elem:
            # a box was clicked
            item = self.identify_row(y)
            if self.tag_has("disabled", item) or self.tag_has("ghost", item):
                return  # do nothing when disabled
            if self.tag_has("unchecked", item) or self.tag_has("tristate", item):
                self._check_ancestor(item)
                self._check_descendant(item)
            elif self.tag_has("checked", item):
                self._uncheck_descendant(item)
                self._uncheck_ancestor(item)
        # if self.saved_node:
        #     self._unsaved_changes(self.saved_node)

    def _unsaved_changes(self, saved):
        checked = self.get_checked()
        for node in saved:
            if node not in checked:
                self.tag_add(node, 'to_remove')
        for node in checked:
            if node not in saved:
                self.tag_add(node, 'to_add')


class App(object):
    def __init__(self, master, path):
        # self.im_checked = ImageTk.PhotoImage(Image.open(IM_CHECKED), master=self)
        self.frame1 = tk.PhotoImage(file='/home/dmitry/Загрузки/XOsX.gif')
        frameCnt = 15
        self.frames = [tk.PhotoImage(file='/home/dmitry/Загрузки/XOsX.gif', format='gif -index %i' % i).subsample(3, 3) for i
                  in range(frameCnt)]
        # self.style = ttk.Style(master)
        # self.style.theme_use("alt")
        # self.style.configure("Treeview", font=("Helvetica", 12))
        self.snapshot = None
        self.last_head = None
        self.is_search_entry = tk.BooleanVar(value=False)
        self._detached = {}
        self.config = {}
        self.saved_node = {}
        self.checked_node = []
        self.ghost = "127.0.0.1"
        self.dirs = {}
        self.nodes = dict()
        self.node = dict()
        self.path = dict()
        self.parent_nodes = {}
        self.master = master
        master.grid_columnconfigure(0, weight=1)
        master.grid_rowconfigure(0, weight=1)
        # for x in range(60):
        #     tk.Grid.columnconfigure(grid, x, weight=1)
        #
        # for y in range(30):
        #     tk.Grid.rowconfigure(grid, y, weight=1)
        frame = ttk.Frame(master)
        self.frame = frame
        # frame.pack(side=tk.TOP, expand=tk.YES, fill=tk.BOTH)
        frame.grid(sticky=tk.NSEW)
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(0, weight=1)
        # style = ttk.Style()
        # style.configure('Checkbox.Treeview', rowheight=24)
        self.tree = CheckBoxTreeview(frame)
        # print(self.tree.winfo_class())
        # self.tree = ttk.Treeview(frame)
        self.tree["columns"] = ("#1", "#2", "#3")
        self.tree.column("#0", minwidth=180, width=350)
        self.tree.column("#1", minwidth=130, width=180)
        self.tree.column("#2", minwidth=180, width=250)
        self.tree.column("#3", minwidth=130, width=180)
        # self.tree.pack(side=tk.TOP, expand=tk.YES, fill=tk.BOTH)
        ysb = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        xsb = ttk.Scrollbar(frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscroll=ysb.set, xscroll=xsb.set)
        self.tree.heading("#0", text="Узлы", )
        # self.tree.heading("#1", text="Статус соединения", anchor=tk.W, command=lambda: self.callback_bbox(1))
        self.tree.heading("#1", text="Статус соединения", anchor=tk.W, command=self.callback_1)
        self.tree.heading("#2", text="Состояние защиты", anchor=tk.W)
        self.tree.heading("#3", text="Статус отслеживания", anchor=tk.W)
        self.tree.grid(row=0, column=0, sticky=tk.NSEW)
        ysb.grid(row=0, column=1, sticky="ns")
        xsb.grid(row=1, column=0, sticky="ew", padx=(5, 0))
        xsb.grid(row=1, column=0, sticky="ew", padx=(5, 0))
        self.button_add()
        self.button_lock()
        self.button_hide()
        self.var_hide.set("Show ALL")
        # self.btn_lock.deselect()
        self.var.set("Locked")

        #self.sizegrip = ttk.Sizegrip(frame)
        #self.sizegrip.grid(row=3, column=1, padx=(0, 5), pady=(0, 5))
        # self.tree.bind("<<TreeviewOpen>>", self.open_node)

        # ysb.pack(side=tk.LEFT)
        # xsb.pack(side=tk.TOP)
        # frame.grid()
        # self.tree.pack(side=tk.LEFT, fill=tk.Y)
        abspath = "/"
        # node = self.tree.insert('', 'end', text='ghost1', open=False)
        # nt = self.tree.insert('', 'end', text='ghost2', open=False)
        # self.insert_node(node, abspath, abspath, client)
        self.bind_func_id = self.tree.bind("<<TreeviewOpen>>", self.open_node)
        #self.tree.bind("<Button-1>", self.tree._box_click, True)
        self.tree.bind("<Motion>", self.mycallback)
        # self.checked_node = [1]
        # self.last_focus = None

    def insert_node(self, parent, text, abspath):

        tags = self.tree.item(parent)["tags"]  # TODO validation ip
        client_ip = None
        for tag in tags:
            if valid_ipv4(tag):
                client_ip = tag

        # if len(text) > 20:
        #     words = text.split()
        #     ch_counter = 0
        #     splittext = []
        #     for word in words:
        #         ch_counter += len(word)
        #         if ch_counter >= 20:
        #             ch_counter = 0
        #         splittext.append(word+'\n')
        #     text = ' '.join(splittext)
        text_with_space = f' {text}'
        node = self.tree.insert(parent, "end", text=text_with_space, open=False)
        self.tree.tag_add(node, client_ip)
        if self.var.get() == "Locked":
            self.tree.tag_add(node, "disabled")
        # print(self.tree.item(node))
        # print('node', node)
        self.node[client_ip][node] = abspath
        self.path[client_ip][abspath] = node
        if abspath in self.dirs[client_ip]:
            self.nodes[client_ip][node] = abspath
            self.tree.insert(node, "end")
        return node

    def open_node(self, event):
        node = self.tree.focus()
        print("open-node called")
        if self.tree.tag_has("disconnected", node):
            return
        tags = self.tree.item(node)["tags"]  # TODO validation ip
        client_ip = None
        for tag in tags:
            if valid_ipv4(tag):
                client_ip = tag
                # self.call_client=client_ip

        # print(f'[open node] call_client, {client_ip}')
        # print('[open node] focus_node', node)
        # print(self.nodes)
        abspath = self.nodes[client_ip].pop(node, None)
        # print('abspath poped', abspath)
        dictdir = {}
        # print("focused item", self.tree.item(node))
        # print("index: ", self.tree.index(node))
        if abspath:
            # print("here")
            for ch in self.tree.get_children(node):
                if self.tree.item(ch)["text"] == "":
                    self.tree.delete(ch)
            for p in self.listdir(
                abspath, client_ip
            ):  # TODO  или как-то переписать листдир для загрузки из конфига?
                if not any(
                    [p in item for item in self.config[client_ip]["watched_files"]]
                ):
                    dictdir[p] = self.insert_node(node, os.path.split(p)[1], p)
        # for abspath in dictdir:
        #     print(abspath, dictdir)
        #     if abspath in self.config[client_ip]['watched_files']:
        #         # self.tree.change_state(node, 'checked')
        #         self.tree._check_ancestor(dictdir[abspath])
        #         self.tree._check_descendant(dictdir[abspath])

    def listdir(self, abspath, host=None):
        return "MOCK"

    def mycallback(self, event):

        tree = event.widget
        head = tree.identify("column", event.x, event.y)
        item = tree.identify_row(event.y)
        tree.tk.call(tree, "tag", "remove", "highlight")
        if self.last_head:
            self.tree.heading(self.last_head, image=False)
        if not item and head:
            self.tree.heading(head, image=self.tree.im_find)
            self.last_head = head
            # if self.is_search_entry.get() and head[1] == '1':
            #     print(f'{head=}')
            #     self.callback_bbox(int(head[1]), reuse=True)


        else:
            tree.tk.call(tree, "tag", "add", "highlight", item)

    def highlight_row(self, event):
        tree = event.widget
        item = tree.identify_row(event.y)
        tree.tk.call(tree, "tag", 'remove', 'highlight')
        tree.tk.call(tree, "tag", 'add', 'highlight', item)

    def callback_1(self):
        self.entry_search = ttk.Entry(self.frame, width=50)
        self.entry_search.insert(0, '1')
        self.entry_search.grid(row=0, column=0, sticky="new", padx=(5, 0))

    def callback_bbox(self, num_head, reuse=None):
        total_width = 0
        for i in range(num_head):
            total_width += self.tree.column(column=f'#{i}', option='width')
        column_width = self.tree.column(column=f'#{num_head}', option='width')
        # print(f'{total_width=}, {column_width=}')
        if not reuse:
            self.entry_search = ttk.Entry(self.tree, width=10)
            self.entry_search.insert(0, '1')
            self.entry_search.place(in_=self.tree, x=(total_width + 30), y=5)
            self.is_search_entry.set(True)
        else:
            self.entry_search.place_configure(x=(total_width + 30))
            print(column_width)
            print(total_width-column_width)
            # self.entry_search.place(in_=self.tree, x=(total_width-column_width - 2), y=5)


    def is_dir(self, abspath):
        pass

    def make_change_window(self):
        pass

    def get_checked(self):
        s = self.tree.get_checked()
        selected = {}
        # print(f"self.tree.get-checked() = {s}")
        for i in s:
            try:
                # print(self.tree.item(i))
                tags = self.tree.item(i)["tags"]  # TODO validation ip
                # client_ip = max(map(lambda x: len(x.split('.')), tags))
                # client_ip, *_ = tags
                client_ip = None
                for tag in tags:
                    if valid_ipv4(tag):
                        client_ip = tag
                        # print("CLIENT IP", client_ip)

                if not client_ip:
                    continue
                # print(self.node)
                # print(self.node[client_ip])
                path = self.node[client_ip][i]
                # print("path", path)

                if client_ip not in selected:
                    selected[client_ip] = [path]
                else:
                    selected[client_ip].append(path)
            except KeyError as e:
                print("ERROR! ", e)
        # print(selected)
        return selected

    def button_add(self):
        self.button = ttk.Button(self.frame, style='Accent.TButton')
        self.button.config(
            text="add", command=self.make_change_window,
        )  # TODO self.send_checked
        self.button.grid(row=2, column=0, sticky="wn", padx=15, pady=(10, 15))

    def button_lock(self):
        self.var = tk.StringVar()
        self.btn_lock = ttk.Checkbutton(self.frame, style='Switch.TCheckbutton')
        self.btn_lock.config(
            onvalue="Unlocked",
            offvalue="Locked",
            variable=self.var,
            textvariable=self.var,
            command=self.toggle,
        )
        self.btn_lock.grid(row=2, column=0, sticky="e")

    def button_hide(self):
        self.var_hide = tk.StringVar()
        self.btn_hide = ttk.Checkbutton(self.frame, style='Switch.TCheckbutton')
        self.btn_hide.config(
            onvalue="Show ALL",
            offvalue="HIDDEN",
            variable=self.var_hide,
            textvariable=self.var_hide,
            command=self.btn_hide_command,
        )
        self.btn_hide.grid(row=2, column=0, sticky="sn")

    def btn_hide_command(self):
        if self.var_hide.get() == "Show ALL":
            self.show_all()
        elif self.var_hide.get() == "HIDDEN":
            self.show_only_selected()

    def toggle(self):  # TODO dict with variables (self.vars = dict())
        if self.var.get() == "ON":
            print("turning on...")
        else:
            print("turning off...")

    def send_checked(self):
        pass

    def show_only_selected(self):
        self.tree.unbind("<<TreeviewOpen>>", self.bind_func_id)

        def _show_recursive(parent):
            self._detached[parent] = []
            for child in self.tree.get_children(parent):
                if self.tree.tag_has("unchecked", child):
                    index = self.tree.index(child)
                    # print(child, index)
                    self.tree.detach(child)
                    self._detached[parent].append((child, index))
                _show_recursive(child)

        for parent in self.parent_nodes:
            _show_recursive(self.parent_nodes[parent])
        #self.toggle()

    def show_all(self):
        self.bind_func_id = self.tree.bind("<<TreeviewOpen>>", self.open_node)
        for parent in self._detached:
            # i = -1
            self._detached[parent].reverse()
            for child in self._detached[parent]:
                # i += 1
                child, index = child
                # print(child, index)
                self.tree.reattach(child, parent, index)
            self._detached[parent].clear()
        self.toggle()

    def show_unsaved_changes(self):

        diff = self.get_diff()


    def get_diff(self):
        return {}
    # def append_from_backup(self, host_ip, ghost):
    #     detached_nodes = {}
    #     for abspath, node in self.saved_node[host_ip].items():
    #         parent = self.tree.parent(node)
    #         self.tree.detach(node)
    #         self.tree.reattach()
    #         detached_nodes[node] = parent
