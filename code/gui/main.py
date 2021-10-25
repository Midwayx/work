import re
import signal
import tkinter as tk
from tkinter import ttk
from tkinter.messagebox import *


def create_list(nt, txt="default"):
    frame = ttk.Frame(nt)
    frame.pack(fill="both", expand=True)
    nt.add(frame, text=txt)
    f = tk.Message(frame, text=txt)
    f.pack(fill=tk.BOTH, expand=tk.YES)

    return frame


class UI(ttk.Frame):
    def __init__(self):
        self.parent = tk.Tk()

        self.parent.tk.call("source", "/home/dmitry/Projects/checker/code/Azure-ttk-theme-gif-based/azure.tcl")
        self.parent.tk.call("set_theme", "light")

        self.parent.minsize("900", "600")  # TODO config
        ttk.Frame.__init__(self, self.parent)
        # self.pack(expand=tk.NO, fill=tk.X, side=tk.TOP)
        self.makeMenuBar()

        self.makeStartPage()
        self.parent.protocol('WM_DELETE_WINDOW', self.iconify)
        signal.signal(signal.SIGUSR1, self.sigusr1_handler)
        # self.mainloop()

    def iconify(self):
        print('Iconify this window!')
        self.parent.withdraw()
        #self.parent.after(5000, self.parent.deiconify)

    def sigusr1_handler(self, signum, frame):
        #print('hi')
        self.parent.deiconify()
        self.parent.update()
        self.parent.grab_set()
        self.parent.focus_set()

    def start(self):
        pass

    def fix_it(self):
        showinfo("Пока не готово", "скоро будет")

    def get_list(self):
        showinfo("Пока не готово", "скоро будет")

    def get_checked(self):
        pass

    def makeMenuBar(self):
        main_menu = tk.Menu()
        self.parent.config(menu=main_menu)
        file_menu = tk.Menu(main_menu, tearoff=0)
        hosts_menu = tk.Menu(file_menu, tearoff=0)
        help_menu = tk.Menu(main_menu, tearoff=0)
        # file_menu.add_command(label='Список узлов', command=self.get_list)
        # file_menu.add_cascade(label='Список узлов', command=self.get_list)
        hosts_menu.add_command(label="Добавить узел", command=self.make_dialog_add)
        hosts_menu.add_command(label="Удалить узел", command=self.fix_it)
        hosts_menu.add_command(label="Список узлов", command=self.get_list)
        help_menu.add_command(label="Помощь", command=self.get_checked)
        main_menu.add_cascade(label="Файл", menu=file_menu)
        main_menu.add_cascade(label="Справка", menu=help_menu)
        file_menu.add_cascade(label="Узлы", menu=hosts_menu)
        # self.mainloop()

    def makeStartPage(self):
        pass

    def add_host(self, ip, name):
        return False, "Error!"

    def make_dialog_add(self):
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Добавить узел")
        self.dialog.minsize("400", "120")
        self.dialog.width = 600
        self.dialog.height = 120
        self.dialog.resizable(width=False, height=False)
        self.dialog.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.ip = tk.StringVar()
        self.name = tk.StringVar()

        # frame = tk.Frame(dialog, bg='#42c2f4', bd=5)
        frame = ttk.Frame(self.dialog, style='Card.TFrame')
        frame.grid(sticky=tk.NSEW, padx=5, pady=5)
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(0, weight=1)
        ip_label = ttk.Label(frame, text="Введите IPv4 адрес узла:")
        name_label = ttk.Label(frame, text="Введите имя узла:")

        name_label.grid(row=0, column=0, sticky="w", padx=5)
        ip_label.grid(row=1, column=0, sticky="w", padx=5)

        self.pattern = re.compile(
            r"^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"
        )

        vcmd = (frame.register(self.validate_ip), "%i", "%P")
        self.name_entry = ttk.Entry(frame, textvariable=self.name)
        self.ip_entry = ttk.Entry(
            frame,
            textvariable=self.ip,
            validate="focus",
            validatecommand=vcmd,
            invalidcommand=self.print_error,
        )
        self.name_entry.grid(row=0, column=1, padx=5, pady=5)
        self.ip_entry.grid(row=1, column=1, padx=5, pady=5)
        self.binds()
        self.message_button = ttk.Button(
            frame, text="send", command=self.send_cmd, state="normal"
        )
        self.message_button.grid(row=2, column=1, padx=5, pady=5, sticky="e")

        self.label_valid = ttk.Label(frame, text="")
        self.label_valid.grid(row=2, column=0, columnspan=2, padx=5, pady=5, sticky="w")

        self.message_button_var = tk.StringVar()
        # self.message_button_var.set('Invalid')
        self.dialog.transient(self.parent)
        # self.dialog.lift()
        self.dialog.grab_set()
        self.dialog.focus_set()
        self.dialog.wait_window()

    def binds(self):
        self.name_entry.bind('<FocusOut>', self.validate_ip1)
        self.name_entry.bind('<FocusIn>', self.validate_ip1)
        self.name_entry.bind('<KeyRelease>', self.validate_ip1)

    def validate_ip1(self, *_):
        if self.name_entry.get() == "":
            self.name_entry.state(["!invalid"])
            print('1')
        else:
            if self.name_entry.get() == 'ghost5':
                self.name_entry.state(["!invalid"])
                print('12')
            else:
                self.name_entry.state(["invalid"])
                print('113')


    def validate_ip(self, index, ip):
        if self.pattern.match(ip) is not None:
            self.message_button_var.set("Valid")
            self.ip_entry.state(["!invalid"])
            # self.message_button.configure(state='active')
            return True
        self.message_button_var.set("Invalid")
        self.ip_entry.state(["invalid"])
        # self.message_button.configure(state='disabled')
        return False

    def print_error(self):
        # print("Запрещенный символ в логине")
        pass

    def send_cmd(self):
        print(self.message_button_var.get())
        if self.validate_ip("0", self.ip.get()):
            print(self.message_button_var.get())
            self.dialog.after(1500, lambda: self.dialog.destroy())
            status = self.add_host(self.ip.get(), self.name.get())
            if status[0]:
                showinfo("Добавлено", "Узел успешно добавлен")
            else:
                showwarning("Внимание!", f"Данный узел уже добавлен как {status[1]}")
        else:
            self.label_valid.configure(text="Invalid IPv4 address. Try again.")
            self.label_valid.after(5500, lambda: self.label_valid.configure(text=""))
            # showinfo('Invalid IPv4', 'You input invalid ipV4 address.\ntry again')


# root window
# root = tk.Tk()
# # root.geometry('400x300')
# root.title('Demo')
# mainmenu = tk.Menu(root)
# root.config(menu=mainmenu)
#
# filemenu = tk.Menu(mainmenu, tearoff=0)
# x = filemenu.add_command(label="Открыть...", command=lambda: create_list(notebook))
# print(x)
# filemenu.add_command(label="Новый")
# filemenu.add_command(label="Сохранить...")
# filemenu.add_command(label="Выход")
#
# helpmenu = tk.Menu(mainmenu, tearoff=0)
# helpmenu.add_command(label="Помощь")
# helpmenu.add_command(label="О программе")
#
# mainmenu.add_cascade(label="Опции",
#                      menu=filemenu)
# mainmenu.add_cascade(label="Справка",
#                      menu=helpmenu)

# a = UI()
# create a notebook
def foo():
    notebook = ttk.Notebook()
    notebook.pack(pady=10, expand=True, fill="both")

    # create frames
    frame1 = ttk.Frame(notebook, width=400, height=280)
    frame2 = ttk.Frame(notebook, width=400, height=280)

    frame1.pack(fill="both", expand=True)
    frame2.pack(fill="both", expand=True)

    # add frames to notebook

    notebook.add(frame1, text="General Information")
    notebook.add(frame2, text="Profile")


# tk.mainloop()
