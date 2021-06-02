import tkinter as tk
from tkinter import ttk
from tkinter.messagebox import showinfo


def create_list(nt, txt='default'):
    frame = ttk.Frame(nt)
    frame.pack(fill='both', expand=True)
    nt.add(frame, text=txt)
    f = tk.Message(frame, text=txt)
    f.pack(fill=tk.BOTH, expand=tk.YES)

    return frame


class UI(tk.Frame):
    def __init__(self, parent=None):
        self.parent = tk.Tk()
        self.parent.minsize('500', '800')  # TODO config
        tk.Frame.__init__(self, parent)
        # self.pack(expand=tk.NO, fill=tk.X, side=tk.TOP)
        self.makeMenuBar()
        self.makeStartPage()
        #self.mainloop()

    def start(self):
        pass

    def get_list(self):
        showinfo('Пока не готово', 'скоро будет')

    def get_checked(self):
        pass

    def makeMenuBar(self):
        main_menu = tk.Menu()
        self.parent.config(menu=main_menu)
        file_menu = tk.Menu(main_menu, tearoff=0)
        file_menu.add_command(label='Список узлов', command=self.get_list)
        help_menu = tk.Menu(main_menu, tearoff=0)
        help_menu.add_command(label='Помощь', command=self.get_checked)
        main_menu.add_cascade(label='Файл', menu=file_menu)
        main_menu.add_cascade(label='Справка', menu=help_menu)
        #self.mainloop()

    def makeStartPage(self):
        pass


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

#a = UI()
# create a notebook
def foo():
    notebook = ttk.Notebook()
    notebook.pack(pady=10, expand=True, fill='both')

    # create frames
    frame1 = ttk.Frame(notebook, width=400, height=280)
    frame2 = ttk.Frame(notebook, width=400, height=280)

    frame1.pack(fill='both', expand=True)
    frame2.pack(fill='both', expand=True)

    # add frames to notebook

    notebook.add(frame1, text='General Information')
    notebook.add(frame2, text='Profile')
# tk.mainloop()


