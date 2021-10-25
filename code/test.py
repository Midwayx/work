import tkinter as tk
import tkinter.ttk as ttk


class TreeBuilder():

    def __init__(self, parent):
        self.parent = parent
        self.build()

    def build(self):

        self.tree = ttk.Treeview(self.parent)

        self.tree["columns"] = ("one", "two")
        self.tree.column("one", width=100)
        self.tree.column("two", width=100)
        self.tree.heading("one", text="coulmn A")
        self.tree.heading("two", text="column B")

        self.tree.insert("", 0, text="Line 1", values=("1A", "1b"))

        id2 = self.tree.insert("", 1, "dir2", text="Dir 2")
        self.tree.insert(id2, "end", "dir 2", text="sub dir 2", values=("2A", "2B"))

        # or alternatively:
        self.tree.insert("", 3, "dir3", text="Dir 3")
        self.tree.insert("dir3", 3, text=" sub dir 3", values=("3A", " 3B"))

        # Here begins the key step
        self.tree.tag_configure('focus', background='yellow')
        self.tree.bind("<Motion>", self.mycallback)

        self.last_focus = None

        # ................................................
        self.tree.pack()

    def mycallback(self, event):

        _iid = self.tree.identify_row(event.y)

        if _iid != self.last_focus:
            if self.last_focus:
                self.tree.item(self.last_focus, tags=[])
            self.tree.item(_iid, tags=['focus'])
            self.last_focus = _iid


if __name__ == '__main__':
    root = tk.Tk()
    tree = TreeBuilder(root)
    root.mainloop()