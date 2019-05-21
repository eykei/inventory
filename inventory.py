'''
description: Inventory Program uses a sqlite3 database with a tkinter GUI to keep track of items.

usage:
1. In the configuration file, specify the name of the database e.g. sample.db (Ok if doesn't exist yet)
2. In the configuration file, specify categories of your inventory
3. Run Inventory Program

status: Working

todo:
'''

from tkinter import *
from tkinter import messagebox
import sqlite3, configparser

config= configparser.ConfigParser()
config.read('config_sample.ini')

inventoryName = config['Settings']['inventoryName']
categories = []
for key, category in config['Categories'].items():
    categories.append(category)
largeFont = ("Verdana", 16)
categories.insert(0, "All")  # add a special category to contain all of the items

conn = sqlite3.connect(inventoryName)
c = conn.cursor()

initialize_db = "CREATE TABLE IF NOT EXISTS \"items\" (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE, category TEXT, accessories TEXT, details TEXT)"
c.execute(initialize_db)


class myClassController(Tk):  # create a class that inherits from Tk()
    def __init__(self):
        Tk.__init__(self)  # initialize the inherited class

        container = Frame(self)  # make a simple containeree
        container.pack(side="top", fill="both", expand=True)  # container fills the window

        # make a dictionary for all the pages
        self.frames = {}

        f3 = EditPage(container, self)
        f1 = StartPage(container, self, f3)
        f2 = AddPage(container, self)

        # add frames to dictionary
        self.frames[StartPage] = f1
        self.frames[AddPage] = f2
        self.frames[EditPage] = f3

        # position these frames right on top of eachother
        f1.grid(row=0, column=0, sticky="nsew")
        f2.grid(row=0, column=0, sticky="nsew")
        f3.grid(row=0, column=0, sticky="nsew")

        # initialize by showing the Start Page
        self.show_frame(StartPage)

    def show_frame(self, page):
        f = self.frames[page]
        f.tkraise()  # bring frame to top


class StartPage(Frame):  # making the start page, inheriting Frame class
    # parent is the container that fills the screen
    # controller is myClassController, which controls the frames to show
    def __init__(self, parent, controller, ep):
        Frame.__init__(self, parent)  # run the inherited class's init method

        # in addition, initialize the following attributes
        title = Label(self, text='Inventory Program v2.0', font=largeFont)
        title.grid(row=0, column=0, columnspan=3, pady=10)

        # create a frame for the item list
        itemListFrame = Frame(self)
        itemListFrame.grid(row=1, column=0, rowspan=4, padx=20)
        self.itemList = Listbox(itemListFrame, selectmode=BROWSE, height=25, width=30)
        self.itemList.pack(side='left')

        scrollbar = Scrollbar(itemListFrame)
        scrollbar.pack(side='right', fill=Y)
        self.itemList.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.itemList.yview)

        self.textBox = Text(self, height=20, width=40, state=DISABLED, wrap=WORD)
        self.textBox.grid(row=1, column=1, columnspan=2, rowspan=2, padx=20, pady=20, sticky="news")

        addButton = Button(self, text="Add", command=lambda: controller.show_frame(
            AddPage))  # need to use lambda function to pass in parameters
        addButton.grid(row=3, column=1, padx=10, pady=5, sticky="news")

        editButton = Button(self, text="Edit", command=lambda: self.editItem(controller, ep))
        editButton.grid(row=3, column=2, padx=10, pady=5, sticky="news")

        deleteButton = Button(self, text="Delete", command=self.deleteItem)
        deleteButton.grid(row=4, column=1, padx=10, pady=5, sticky="news")

        hideButton = Button(self, text="Hide", command=self.hide)
        hideButton.grid(row=4, column=2, padx=10, pady=5, sticky='news')

        viewButton = Button(self, text="View", command=self.viewItem)
        viewButton.grid(row=5, column=2, padx=10, pady=5, sticky="news")

        refreshButton = Button(self, text="Refresh", command=self.refresh)
        refreshButton.grid(row=5, column=1, padx=10, pady=5, sticky="news")

        self.categoryVar = StringVar()
        self.categoryVar.set(categories[0])
        option = OptionMenu(self, self.categoryVar, *categories)  # unpack categories list
        option.grid(row=5, column=0, padx=10, pady=5, sticky="news")

        searchFrame = Frame(self)
        searchFrame.grid(row=6, column=0)

        self.searchTerm = StringVar()
        self.searchBox = Entry(searchFrame, textvariable=self.searchTerm, width=28)
        self.searchBox.pack(side='left')

        searchButton = Button(searchFrame, text="Search", command=self.search)
        searchButton.pack(side='right')

        self.lastAddedVar = StringVar()
        self.lastAddedLabel = Label(self, textvariable=self.lastAddedVar)
        self.lastAddedLabel.grid(row=6, column=1, columnspan=2)

        self.itemCountVar = StringVar()
        self.itemCountLabel = Label(self, textvariable=self.itemCountVar)
        self.itemCountLabel.grid(row=7, column=1, columnspan=2)

        self.refresh()

    def search(self):
        searchTerm = "%"+self.searchTerm.get()+"%"  # add wildcard characters to search term

        c.execute("SELECT * FROM items WHERE name LIKE ?", (searchTerm, ))

        self.itemList.delete(0, END)

        count = 0
        for item in c.fetchall():
            self.itemList.insert(END, item[1])
            count += 1

        self.itemCountVar.set('Item Count: '+str(count))

        # clear the text box
        self.textBox.config(state=NORMAL)
        self.textBox.delete(1.0, END)
        self.textBox.config(state=DISABLED)

        self.searchBox.delete(0, END)

    def viewItem(self):
        try:
            index = self.itemList.curselection()[0]
        except IndexError:
            messagebox.showwarning("Error", "No Item Selected")
            return
        selectName = self.itemList.get(index)
        c.execute("SELECT * FROM items WHERE name = ?", (selectName,))
        id, name, cat, acc, det = c.fetchall()[0]

        acc1 = acc.replace(',', '\n')
        det1 = det.replace(',', '\n')

        info = "Name:\t\t%s\n\nCategory:\t\t%s\n\nAccessories:\n %s\n\nDetails:\n %s" % (name, cat, acc1, det1)

        self.textBox.config(state=NORMAL)
        self.textBox.delete(1.0, END)
        self.textBox.insert(END, info)
        self.textBox.config(state=DISABLED)

    def refresh(self):

        try:
            # retrieve name of last added item
            c.execute("SELECT MAX(id) FROM items")
            max_id = c.fetchone()[0]
            c.execute("SELECT * FROM items where id = ?", (max_id,))
            self.lastAddedVar.set("Last Added: " + c.fetchone()[1])
        except TypeError:
            self.lastAddedVar.set("Last Added: None")

        # populate the list box with items according to category selected

        # get category
        category = self.categoryVar.get()
        # clear item list
        self.itemList.delete(0, END)

        if category == 'All':
            c.execute("SELECT * FROM items")
        else:
            c.execute("SELECT * FROM items WHERE category = ?", (category, ))

        count = 0
        for item in c.fetchall():
            self.itemList.insert(END, item[1])
            count += 1

        self.itemCountVar.set('Item Count: '+str(count))

        # clear the text box
        self.textBox.config(state=NORMAL)
        self.textBox.delete(1.0, END)
        self.textBox.config(state=DISABLED)

    def deleteItem(self):
        try:
            index = self.itemList.curselection()[0]
        except IndexError:
            messagebox.showwarning("Error", "No Item Selected")
            return
        selectName = self.itemList.get(index)
        c.execute("DELETE FROM items WHERE name = ?", (selectName,))
        conn.commit()
        self.itemList.delete(ACTIVE)

    def hide(self):
        index = self.itemList.curselection()[0]
        self.itemList.delete(index)

    def editItem(self, controller, ep):
        try:
            index = self.itemList.curselection()[0]
        except IndexError:
            messagebox.showwarning("Error", "No Item Selected")
            return
        selectName = self.itemList.get(index)
        c.execute("SELECT * FROM items WHERE name = ?", (selectName,))
        id, name, cat, acc, det = c.fetchall()[0]

        # we edit the editPage that we passed in

        ep.id = id

        ep.e1.delete(0, END)
        ep.e2.delete(0, END)
        ep.e3.delete(0, END)
        ep.e4.delete(0, END)

        ep.e1.insert(0, name)
        ep.e2.insert(0, cat)
        ep.e3.insert(0, acc)
        ep.e4.insert(0, det)

        controller.show_frame(EditPage)


class AddPage(Frame):
    def __init__(self, parent, controller):
        Frame.__init__(self, parent)  # run the inherited class's init method
        title = Label(self, text='Add Item', font=largeFont)
        title.grid(row=0, column=0, columnspan=2, pady=10)

        self.message = StringVar()
        self.messageLabel = Label(self, textvariable=self.message)
        self.messageLabel.grid(row=1, column=0, columnspan=2)

        wLabel = 20  # width of labels
        Label(self, text='Name: ', width=wLabel).grid(row=2, column=0, padx=10)
        Label(self, text='Category: ', width=wLabel).grid(row=3, column=0, padx=10)
        Label(self, text='Accessories: ', width=wLabel).grid(row=4, column=0, padx=10)
        Label(self, text='Details: ', width=wLabel).grid(row=5, column=0, padx=10)

        self.nameVar = StringVar()
        self.e1 = Entry(self, textvariable=self.nameVar, width=40)
        self.e1.grid(row=2, column=1, padx=10, pady=40)

        self.catVar = StringVar()
        self.e2 = Entry(self, textvariable=self.catVar, width=40)
        self.e2.grid(row=3, column=1, padx=10, pady=40)

        self.accVar = StringVar()
        self.e3 = Entry(self, textvariable=self.accVar, width=40)
        self.e3.grid(row=4, column=1, padx=10, pady=40)

        self.detVar = StringVar()
        self.e4 = Entry(self, textvariable=self.detVar, width=40)
        self.e4.grid(row=5, column=1, padx=10, pady=40)

        Button(self, text='Back', command=lambda: self.back(controller), width=10).grid(
            row=6, columnspan=2, sticky='e', ipadx=10, ipady=10, padx=10)
        Button(self, text='Save', command=self.saveInfo, width=10).grid(
            row=6, columnspan=2, sticky='s', padx=10, ipadx=10, ipady=10)

    def back(self, controller):
        self.message.set("")
        controller.show_frame(StartPage)

    def saveInfo(self):

        if self.catVar.get() not in categories:
            self.message.set("Invalid Category")
            return

        try:
            # Pass null as first value, the id # is autogenerated by sql
            c.execute("INSERT INTO items VALUES (?,?,?,?,?)",
                      (None, self.nameVar.get(), self.catVar.get(), self.accVar.get(), self.detVar.get()))

            conn.commit()
            self.message.set("Item Added!")

        except sqlite3.IntegrityError:
            self.message.set("Item already exists!")
            return

        self.e1.delete(0, END)
        self.e2.delete(0, END)
        self.e3.delete(0, END)
        self.e4.delete(0, END)


# create editpage by inheriting attributes/methods from addpage
class EditPage(AddPage):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        title = Label(self, text='Edit Item', font=largeFont)
        title.grid(row=0, column=0, columnspan=2, pady=10)
        self.id = ""

    def saveInfo(self):
        if self.catVar.get() not in categories:
            self.message.set("Invalid Category")
            return

        c.execute("UPDATE items SET name = :name, category = :cat, accessories = :acc, details = :det WHERE id = :id ",
                  {"id": self.id, "name": self.nameVar.get(), "cat": self.catVar.get(), "acc": self.accVar.get(), "det": self.detVar.get()})
        conn.commit()

        self.message.set("Item Updated!")


app = myClassController()  # this is our custom 'root' since myClassController inherits Tk()
app.geometry("610x610+300+0")
app.wm_title('Inventory Program')
app.mainloop()