import tkinter
import gui.treewindow


win = tkinter.Tk()

win.title("Отображение дерева структуры каталогов")
win.geometry("900x400+200+50")

# В пути используются косые черты / вместо обратных косых черт \, чтобы путь к файлу можно было полностью сохранить
path = r"/home/"

infoWin = gui.treewindow.InfoWindow(win)
treeWin = gui.treewindow.TreeWindow(win, path, infoWin)

win.mainloop()
