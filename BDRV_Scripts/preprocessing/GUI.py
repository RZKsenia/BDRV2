from tkinter import *
from tkinter import filedialog
from tkinter import messagebox
from tkinter import ttk
import io
import time

from PIL import Image, ImageTk

from BDRV_Scripts.preprocessing.MainScript import Modeller # класс для работы с нейросетью
from BDRV_Scripts.preprocessing.MnemoObj import MnemoObj # класс объекта мнемосхемы
from BDRV_Scripts.preprocessing.MnemoLineObj import MnemoLineObj # класс линии в мнемосхеме
from BDRV_Scripts.preprocessing.MnemoObjList import MnemoObjList # класс списка объектов мнемосхемы
from BDRV_Scripts.preprocessing.SVGBuilder import SVGBuilder # класс генерации и экспорта мнемосхемы в SVG

class GUI(object):
    """
    Класс для построения графического интерфейса программного обеспечения.
    Включает в себя также методы обработки событий.
    """
    def __init__(self):
        self.path_to_config_file = r'C:/Python_projects/BDRV2/config/bdrv_config.txt'
        self.path_to_uploaded_screenshot = '' # здесь будем хранить путь к скриншоту мнемосхемы
        self.obj_colors = {}  # словарь для хранения цветов объектов
        self.path_to_image_with_objects = ""  # путь к изображению с обнаруженными объектами
        self.canvas_with_objects = None  # канва, на которой работаем с найденными объектами
        self.display_image = None  # отображаемая картинка в Canvas
        self.ph = None  # отображаемый прямоугольник поверх объекта
        self.rect = None  # прямоугольник для обводки объекта мнемосхемы под курсором
        self.dd_x_coord_begin = 0 # х координата начала Drag&Drop
        self.dd_y_coord_begin = 0 # y координата начала Drag&Drop
        self.btn_pushed = 0 # 1 если левая кнопка мыши нажата, 0 если отжата
        self.create_object = 0 # 1 - начинаем создавать объект
        self.zoomer_x = 0 # координата х окна увеличения
        self.zoomer_y = 0 # координата у окна увеличения

        self.mnemo_obj_list = MnemoObjList() # объекты мнемосхемы
        self.mnemo_lines_list = MnemoObjList() # линии мнемосхемы
        self.current_mn_obj = None # текущий выделенный мышью объект мнемосхемы
        self.group_selected_flag = 0 # флаг, указывающий на групповое выделение объектов
        self.key_pressed_code = None # код нажатой клавиши
        self.Md = Modeller()  # класс для работы с нейросетью

        self.window = Tk() # главное окно интерфейса
        self.frame_right_menu = ttk.Frame(self.window, width=200)
        self.frame_right_menu_object_properties = ttk.Frame(self.frame_right_menu)
        vbar = Scrollbar(self.frame_right_menu, orient=VERTICAL)
        vbar.pack(side=RIGHT, fill=Y)
        self.tab_control = ttk.Notebook(self.window)  # вкладки на главном окне
        self.lbl_tree = ttk.Label(self.frame_right_menu, text='Объекты мнемосхемы:')
        self.obj_tree = ttk.Treeview(self.frame_right_menu)

        self.window.title("Автомнемо")
        self.window.geometry('1000x650')

        self.obj_tree.configure(yscrollcommand=vbar.set)
        self.frame_right_menu.pack(side=RIGHT, fill=Y)

        self.canvas_zoomer = Canvas(self.frame_right_menu)


        self.tab1 = ttk.Frame(self.tab_control)
        self.tab2 = ttk.Frame(self.tab_control)
        self.tab3 = ttk.Frame(self.tab_control)

        self.lbl_tree.pack(side=TOP)

        self.obj_tree.master = self.frame_right_menu

        self.obj_tree["columns"] = ("one", "two", "three", "four")
        self.obj_tree.column("#0", width=100, minwidth=20)
        self.obj_tree.column("one", width=70, minwidth=10)
        self.obj_tree.column("two", width=70, minwidth=20)
        self.obj_tree.column("three", width=70, minwidth=20)

        self.obj_tree.heading("#0", text="Имя")
        self.obj_tree.heading("one", text="Обозначение")
        self.obj_tree.heading("two", text="X")
        self.obj_tree.heading("three", text="Y")

        # Level 1
        self.folder1 = self.obj_tree.insert("", 0, "collon", text="Колонны", values=("collon", "", "", ""))
        self.folder2 = self.obj_tree.insert("", 1, "heat-exchanger", text="Теплообменники",
                                            values=("heat-exchanger", "", "", ""))
        self.folder3 = self.obj_tree.insert("", 2, "indicator", text="Индикаторы", values=("indicator", "", "", ""))
        self.folder4 = self.obj_tree.insert("", 3, "pump", text="Насосы", values=("pump", "", "", ""))
        self.folder5 = self.obj_tree.insert("", 4, "tank", text="Резервуары", values=("tank", "", "", ""))
        self.folder6 = self.obj_tree.insert("", 5, "valve", text="Арматура", values=("valve", "", "", ""))
        self.folder7 = self.obj_tree.insert("", 6, "text", text="Текст", values=("text", "", "", ""))
        self.obj_tree.pack(side=TOP)

        self.frame_right_menu_object_properties.pack(side=TOP)
        self.lbl_mn_obj = ttk.Label(self.frame_right_menu_object_properties, text='Свойства объекта:')
        self.lbl_mn_obj.pack(side=TOP)

        self.frame_right_menu_object_name_type = ttk.Frame(self.frame_right_menu)
        self.frame_right_menu_object_name_type.pack(side=TOP)
        self.frame_right_menu_name = ttk.Frame(self.frame_right_menu_object_name_type)
        self.frame_right_menu_name.pack(side=LEFT)
        self.lbl_objName = ttk.Label(self.frame_right_menu_name, text='Имя объекта:')
        self.lbl_objName.pack(side=TOP)
        self.txtObjName = ttk.Entry(self.frame_right_menu_name)
        self.txtObjName.pack(side=TOP)
        self.frame_right_menu_title = ttk.Frame(self.frame_right_menu_object_name_type)
        self.frame_right_menu_title.pack(side=LEFT)
        self.lblObjTitle = ttk.Label(self.frame_right_menu_title, text='Обозначение:')
        self.lblObjTitle.pack(side=TOP)
        self.txtObjTitle = ttk.Entry(self.frame_right_menu_title)
        self.txtObjTitle.pack(side=TOP)
        self.frame_right_menu_type = ttk.Frame(self.frame_right_menu_object_name_type)
        self.frame_right_menu_type.pack(side=LEFT)
        self.lblObjType = ttk.Label(self.frame_right_menu_type, text='Тип объекта:')
        self.lblObjType.pack(side=TOP)
        self.cmbxObjType = ttk.Combobox(self.frame_right_menu_type)
        self.cmbxObjType['values'] = ('collon',
                                      'heat-exchanger',
                                      'indicator',
                                      'pump',
                                      'tank',
                                      'valve',
                                      'text')
        self.cmbxObjType.pack(side=TOP)


        self.frame_right_menu_object_coordinates = ttk.Frame(self.frame_right_menu)
        self.frame_right_menu_object_coordinates.pack(side=TOP)
        self.lblcoord = ttk.Label(self.frame_right_menu_object_coordinates, text='Координаты объекта:')
        self.lblcoord.pack(side=LEFT)
        self.lblX = ttk.Label(self.frame_right_menu_object_coordinates, text='x:')
        self.lblX.pack(side=LEFT)
        self.lblXval = ttk.Label(self.frame_right_menu_object_coordinates, text='')
        self.lblXval.pack(side=LEFT)
        self.lblY = ttk.Label(self.frame_right_menu_object_coordinates, text='y:')
        self.lblY.pack(side=LEFT)
        self.lblYval = ttk.Label(self.frame_right_menu_object_coordinates, text='')
        self.lblYval.pack(side=LEFT)

        self.frame_right_menu_buttons_region = ttk.Frame(self.frame_right_menu)
        self.frame_right_menu_buttons_region.pack(side=TOP)
        self.btnSaveObj = ttk.Button(self.frame_right_menu_buttons_region, text='Сохранить изменения')
        self.btnSaveObj.pack(side=LEFT)
        self.btnMergeObjects = ttk.Button(self.frame_right_menu_buttons_region, text='Объеденить объекты')
        self.btnMergeObjects.pack(side=LEFT)
        self.btnDelObj = ttk.Button(self.frame_right_menu_buttons_region, text='Удалить объект')
        self.btnDelObj.pack(side=LEFT)

        self.frame_right_menu_create_object_region = ttk.Frame(self.frame_right_menu)
        self.frame_right_menu_create_object_region.pack(side = TOP)
        self.lblCreateObj = ttk.Label(self.frame_right_menu_create_object_region, text='Создать объект')
        self.lblCreateObj.pack(side = TOP)
        self.frame_right_menu_create_name_type = ttk.Frame(self.frame_right_menu_create_object_region)
        self.frame_right_menu_create_name_type.pack(side = TOP)
        self.frame_right_menu_create_name = ttk.Frame(self.frame_right_menu_create_name_type)
        self.frame_right_menu_create_name.pack(side=LEFT)
        self.lblCreateName = ttk.Label(self.frame_right_menu_create_name, text='Имя объекта:')
        self.lblCreateName.pack(side=TOP)
        self.txtNewObjName = ttk.Entry(self.frame_right_menu_create_name)
        self.txtNewObjName.pack(side=TOP)
        self.frame_right_menu_create_title = ttk.Frame(self.frame_right_menu_create_name_type)
        self.frame_right_menu_create_title.pack(side=LEFT)
        self.lblCreateTitle = ttk.Label(self.frame_right_menu_create_title, text='Обозначение объекта:')
        self.lblCreateTitle.pack(side=TOP)
        self.txtNewObjTitle = ttk.Entry(self.frame_right_menu_create_title)
        self.txtNewObjTitle.pack(side=TOP)
        self.frame_right_menu_create_type = ttk.Frame(self.frame_right_menu_create_name_type)
        self.frame_right_menu_create_type.pack(side=LEFT)
        self.lblCreateType = ttk.Label(self.frame_right_menu_create_type, text='Тип объекта:')
        self.lblCreateType.pack(side=TOP)
        self.cmbxNewObjType = ttk.Combobox(self.frame_right_menu_create_type)
        self.cmbxNewObjType['values'] = ('collon',
                                      'heat-exchanger',
                                      'indicator',
                                      'pump',
                                      'tank',
                                      'valve',
                                      'text')
        self.cmbxNewObjType.pack(side=TOP)
        self.btnCreateObj = ttk.Button(self.frame_right_menu_create_object_region, text='Создать объект')
        self.btnCreateObj.pack(side = TOP)

        # Вкладки:
        self.tab_control.add(self.tab1, text='Скриншот мнемосхемы')
        self.tab_control.add(self.tab2, text='Обнаруженные объекты')
        self.tab_control.add(self.tab3, text='Обнаруженные линии')
        self.tab_control.pack(expand=1, fill='both')

        # читаем файл конфигурации:
        with io.open(self.path_to_config_file) as config:
            row = config.readline()
            row = config.readline()
            row = row.split(' ')
            # базовый цвет - цвет фона мнемосхемы
            self.Md.baseColor = (int(row[0]), int(row[1]), int(row[2].rstrip('\n')))
            row = config.readline()
            row = config.readline()
            # цыета линий:
            while row != '===objects-colors:===\n':
                row = row.split(' ')
                self.Md.lines_colors.append((int(row[0]), int(row[1]), int(row[2]), row[3].rstrip('\n')))
                row = config.readline()
            # цвета объектов:
            row = config.readline()
            while row != '=== end of objects-colors ===\n':
                row = row.split(' ')
                if row[0] != '===':
                    self.Md.obj_colors[row[0]] = (int(row[1]), int(row[2]), int(row[3]))
                    self.obj_colors[row[0]] = row[4].rstrip('\n')
                else:
                    break
                row = config.readline()
            config.close()

    def build_window(self):
        """
            Функция построения окна программы
        """
        # Главное меню:
        menu = Menu(self.window)
        new_item = Menu(menu)
        new_item.add_command(label = 'Загрузить скриншот мнемосхемы', command = lambda: self.upload_screenshot(self))
        new_item.add_command(label = 'Запустить обнаружение объектов', command = lambda: self.detect_objects(self))
        new_item.add_separator()
        new_item.add_command(label = 'Сохранить найденные контуры в файл', command=lambda: self.save_found_contours(self))
        new_item.add_command(label = 'Открыть файл с контурами', command=lambda: self.open_found_contours(self))
        new_item.add_separator()
        new_item.add_command(label='Экспортировать в SVG', command=lambda: self.generate_svg_file(self))

        menu.add_cascade(label = 'Файл', menu=new_item)
        self.window.config(menu = menu)

        self.window.mainloop()

    def upload_screenshot(self, file=None):
        """
        Функция команды меню - Загрузить файл мнемосхемы.
        Загружается файл и выводится на первую вкладку в окне программы
        """
        # получаем имя файла:
        if file == None:
            filename = filedialog.askopenfilename(filetypes = (("png files","*.png"),("all files","*.*")))
            tab = self.tab1
        else:
            # открываем файл с обнаруженными ранее объектами мнемосхемы
            filename = file
            tab = self.tab2
        screenshot = Image.open(filename)
        self.path_to_uploaded_screenshot = filename # сохраняем путь к скриншоту для дальнейшего использования

        self.upload_image(self, screenshot, tab)

    def detect_objects(self):
        """
        Функция обнаружения объектов на скриншоте
        """
        if self.path_to_uploaded_screenshot == "":
            messagebox.showinfo('Ошибка поиска объектов', 'Загрузите файл мнемосхемы')
            return
        else:
            messagebox.showinfo('Обнаружение объектов', 'Поиск объектов может занять некоторое время. Подождите.')
            # проводим анализ загруженного скриншота:
            self.Md.analize_screenshot(self.path_to_uploaded_screenshot)
            self.save_found_contours(self) #сохраняем найденные контуры
            self.open_found_contours(self) # загружаем только что сохранённый файл и отображаем контуры
            self.tab2.focus()

    def upload_image(self, screenshot, tab_obj):
        """
        Функция вывода изображения (screenshot) на вкладку (tab)
        """
        frame = Frame(tab_obj)
        frame.pack(expand=True, fill=BOTH)

        self.vbar = Scrollbar(frame, orient=VERTICAL)
        self.vbar.pack(side=RIGHT, fill=Y)
        self.hbar = Scrollbar(frame, orient=HORIZONTAL)
        self.hbar.pack(side=BOTTOM, fill=X)
        self.canvas_with_objects = Canvas(frame,
                                          yscrollcommand=self.vbar.set,
                                          xscrollcommand=self.hbar.set)
        self.canvas_with_objects.pack(side=LEFT, expand=True, fill=BOTH)

        # Сохраняем картинку в переменную класса, чтобы сборщик мусора её не уничтожил раньше времени:
        self.display_image = ImageTk.PhotoImage(screenshot)

        width = screenshot.width
        height = screenshot.height
        self.resized_image = ImageTk.PhotoImage(screenshot.resize((width*2, height*2), Image.ANTIALIAS))

        self.canvas_with_objects.config(width=screenshot.width, height=screenshot.height)
        self.canvas_with_objects.config(scrollregion=(0, 0, screenshot.width, screenshot.height))
        self.canvas_with_objects.create_image(screenshot.width / 2,
                                              screenshot.height / 2,
                                              image=self.display_image)
        self.canvas_zoomer.pack(side=TOP)
        self.canvas_zoomer.create_image(width * 5,
                                        height * 5,
                                        image= self.resized_image)

        # отслеживаем координаты курсора, нажатые клавиши:
        self.canvas_with_objects.bind("<Motion>", lambda event: self.on_over_the_object_move(self, event))
        self.canvas_with_objects.bind("<Button-1>", lambda event: self.on_click_on_canvas(self, event))
        self.canvas_with_objects.bind("<ButtonRelease-1>", lambda event: self.end_drag_and_drop(self, event))

        self.obj_tree.bind("<ButtonRelease-1>", lambda event: self.on_click_on_tree(self, event))

        self.btnSaveObj.bind("<Button-1>", lambda event: self.save_changes_in_object(self, event))
        self.btnMergeObjects.bind("<Button-1>", lambda event: self.merge_objects(self, event))
        self.btnDelObj.bind("<Button-1>", lambda event: self.delete_selected_object(self, event))
        self.btnCreateObj.bind("<Button-1>", lambda event: self.create_new_object(self, event))

        # полосы прокрутки:
        self.vbar.config(command=self.canvas_with_objects.yview)
        self.hbar.config(command=self.canvas_with_objects.xview)

    def insert_obj_into_tree(self, mn_obj):
        """
        Вставить объект в дерево объектов.
        mn_obj: объект типа MnemoObj
        """
        if mn_obj.type == "collon":
            self.obj_tree.insert(self.folder1,
                                 "end",
                                 mn_obj.obj_name,
                                 text=mn_obj.obj_name,
                                 values=(mn_obj.obj_title, mn_obj.x, mn_obj.y))
        else:
            if mn_obj.type == "heat-exchanger":
                self.obj_tree.insert(self.folder2,
                                     "end",
                                     mn_obj.obj_name,
                                     text=mn_obj.obj_name,
                                     values=(mn_obj.obj_title, mn_obj.x, mn_obj.y))
            else:
                if mn_obj.type == "indicator":
                    self.obj_tree.insert(self.folder3,
                                         "end",
                                         mn_obj.obj_name,
                                         text=mn_obj.obj_name,
                                         values=(mn_obj.obj_title, mn_obj.x, mn_obj.y))
                else:
                    if mn_obj.type == "pump":
                        self.obj_tree.insert(self.folder4,
                                             "end",
                                             mn_obj.obj_name,
                                             text=mn_obj.obj_name,
                                             values=(mn_obj.obj_title, mn_obj.x, mn_obj.y))
                    else:
                        if mn_obj.type == "tank":
                            self.obj_tree.insert(self.folder5,
                                                 "end",
                                                 mn_obj.obj_name,
                                                 text=mn_obj.obj_name,
                                                 values=(mn_obj.obj_title, mn_obj.x, mn_obj.y))
                        else:
                            if mn_obj.type == "valve":
                                self.obj_tree.insert(self.folder6,
                                                     "end",
                                                     mn_obj.obj_name,
                                                     text=mn_obj.obj_name,
                                                     values=(mn_obj.obj_title, mn_obj.x, mn_obj.y))
                            else:
                                self.obj_tree.insert(self.folder7,
                                                     "end",
                                                     mn_obj.obj_name,
                                                     text=mn_obj.obj_name,
                                                     values=(mn_obj.obj_title, mn_obj.x, mn_obj.y))

    def select_objects_in_tree(self, mn_obj):
        """
        Выделить объекты в дереве объектов
        """
        if len(self.obj_tree.selection()) > 0:
            self.obj_tree.selection_remove(self.obj_tree.selection()[0])
        self.obj_tree.selection_add(mn_obj.obj_name)

    def on_click_on_tree(self, event):
        """
        При выделении объекта в дереве - выделить объект визуально на картинке
        """
        selected_obj_name = self.obj_tree.selection()
        mn_onj_name = selected_obj_name[0]
        print(mn_onj_name)
        searched_obj = self.mnemo_obj_list.search(obj_name=mn_onj_name)

        if (self.mnemo_obj_list is not None) & (searched_obj is not None):
            # список объектов мнемосхемы не пуст, и среди объектов найден выделенный
            # обводим объект белым прямоугольником:
            self.on_over_the_object_move(self, event, obj_name= mn_onj_name)
            # заполняем элементы управления свойствами выделенного объекта:
            self.fill_name_and_type_of_object(self, mn_obj= searched_obj)
            # обновляем текущий выделенный объект
            self.current_mn_obj = searched_obj

    def clear_tree(self):
        """
        удаляем все элементы дочерние из дерева объектов
        """
        el = self.mnemo_obj_list.head
        while el is not None:
            self.obj_tree.delete(el.key.obj_name) # удаляем объект по имени
            el = el.next

    def refresh_tree(self):
        """
        обновление дерева объектов
        """
        el = self.mnemo_obj_list.head
        while el is not None:
            self.insert_obj_into_tree(self, mn_obj=el.key) # вставляем объект в дерево
            el = el.next

    def on_over_the_object_move(self, event, obj_name = None):
        """
        При наведении курсора мыши на объект мнемосхемы - он выделяется
        в дереве объектов, а также выделяется цветом на самой мнемосхеме
        """
        if self.btn_pushed == 1:
            if self.create_object == 0:
                # рисуем прямоугольник выделения
                self.canvas_with_objects.delete("selector")
                self.canvas_with_objects.create_rectangle(self.dd_x_coord_begin,
                                                          self.dd_y_coord_begin,
                                                          self.canvas_with_objects.canvasx(event.x),
                                                          self.canvas_with_objects.canvasy(event.y),
                                                          outline='yellow',
                                                          width=1,
                                                          tag="selector")
            else:
                # рисуем прямоугольник выделения
                self.canvas_with_objects.delete("selector")
                self.canvas_with_objects.create_rectangle(self.dd_x_coord_begin,
                                                          self.dd_y_coord_begin,
                                                          self.canvas_with_objects.canvasx(event.x),
                                                          self.canvas_with_objects.canvasy(event.y),
                                                          outline='lime',
                                                          width=1,
                                                          tag="selector")

        if self.mnemo_obj_list is not None:
            # находим - есть ли объект мнемосхемы по этим координатам:
            if obj_name == None:
                mn_obj = self.mnemo_obj_list.search(x=self.canvas_with_objects.canvasx(event.x),
                                                    y=self.canvas_with_objects.canvasy(event.y))
            else:
                mn_obj = self.mnemo_obj_list.search(obj_name=obj_name)
            # Если объект мнемосхемы найден:
            if mn_obj is not None:
                self.paint_white_rectangle_around_object(self, event, mn_obj= mn_obj)
            else:
                # удаляем нарисованный ранее белый прямоугольник:
                self.canvas_with_objects.delete(self.canvas_with_objects.find_withtag('white_rectangle'))

    def paint_zoomer(self, event):
        """
        прорисовка прямоугольника "увеличительного стекла"
        """
        self.canvas_with_objects.delete('zoomer')
        self.rect = self.canvas_with_objects.create_rectangle(self.zoomer_x,
                                                              self.zoomer_y,
                                                              100,
                                                              100,
                                                              outline='red',
                                                              width=7,
                                                              tag='zoomer')

    def paint_white_rectangle_around_object(self, event, mn_obj):
        """
        нарисовать белый прямоугольник вокруг объекта
        """
        # удаляем нарисованные ранее прямоугольники:
        self.canvas_with_objects.delete('white_rectangle')
        # курсор попал на объект - обводим его прямоугольником
        self.rect = self.canvas_with_objects.create_rectangle(mn_obj.x, mn_obj.y,
                                                              mn_obj.x + mn_obj.width,
                                                              mn_obj.y + mn_obj.height,
                                                              outline='white',
                                                              width=5,
                                                              tag='white_rectangle')

    def repaint_frames_around_objects(self):
        """
        перерисовка рамок вокруг объектов мнемосхемы
        tag_addition - приставка, которая если не пуста, используется для выделенных объектов
        selection_color - цвет выделения объектов
        """
        self.canvas_with_objects.delete('title')

        # прорисовываем рамки обнаруженных     
        if len(self.mnemo_obj_list) != 0:
            cur_val = self.mnemo_obj_list.head

            while cur_val is not None:
                if cur_val.key.selected_flag == 0:
                    color = self.obj_colors[cur_val.key.type]  # получаем цвет рамки в зависимости от типа объекта
                    tag = cur_val.key.type + '-' + cur_val.key.obj_name
                else:
                    color = "aqua"
                    tag = "selected-" + cur_val.key.obj_name
                self.canvas_with_objects.delete(tag) # если объект был ранее создан, то удаляем его
                # обводим объекты рамками:
                self.canvas_with_objects.create_rectangle(cur_val.key.x,
                                                          cur_val.key.y,
                                                          cur_val.key.x + cur_val.key.width,
                                                          cur_val.key.y + cur_val.key.height,
                                                          outline= color,
                                                          width= 3,
                                                          tag= tag)
                # выводим описание объекта
                if cur_val.key.obj_title != '':
                    self.canvas_with_objects.create_text(cur_val.key.x + cur_val.key.width/2,
                                                         cur_val.key.y + cur_val.key.height/2,
                                                         fill = color,
                                                         text = cur_val.key.obj_title,
                                                         tags = 'title-'+cur_val.key.obj_title
                                                         )
                cur_val = cur_val.next

        if len(self.mnemo_lines_list) != 0:
            # прорисовываем линии
            cur_line = self.mnemo_lines_list.head

            while cur_line is not None:
                color = cur_line.key.line_color
                self.canvas_with_objects.create_line(
                                cur_line.key.x1,
                                cur_line.key.y1,
                                cur_line.key.x2,
                                cur_line.key.y2,
                                fill = color,
                                width = 2,
                                tags = 'line'
                )
                cur_line = cur_line.next

        self.paint_zoomer(self, event= None)

    def fill_name_and_type_of_object(self, mn_obj):
        """
        заполнение элементов управления данными об объекте
        """
        # очищаем элементы управления:
        self.txtObjName.delete(0, END)
        self.cmbxObjType.delete(0, END)
        self.txtObjTitle.delete(0, END)
        # Имя объекта (уникально):
        self.txtObjName.insert(0, mn_obj.obj_name)
        # тип объекта:
        self.cmbxObjType.insert(0, mn_obj.type)
        # описание объекта (также уникально):
        self.txtObjTitle.insert(0, mn_obj.obj_title)

    def on_click_on_canvas(self, event):
        """
        Обработка клика
        Если кликнули по какому-то объекту, то в соответствующие
        элементы управления выводим информацию об объекте, а также
        выделяем его в дереве объектов
        """
        # сохраняем координаты, т.к. это может быть начало Drag&Drop
        self.dd_x_coord_begin = self.canvas_with_objects.canvasx(event.x)
        self.dd_y_coord_begin = self.canvas_with_objects.canvasy(event.y)
        self.btn_pushed = 1


        if self.mnemo_obj_list is not None:
            if self.create_object == 0:
                # находим - есть ли объект мнемосхемы по этим координатам:
                mn_obj = self.mnemo_obj_list.search(x=self.dd_x_coord_begin, y=self.dd_y_coord_begin)

                if mn_obj is not None:
                    # если по координатам найден объект мнемосхемы,
                    # то прописываем значения его свойств в элементы управления.
                    self.fill_name_and_type_of_object(self, mn_obj)
                    self.select_objects_in_tree(self, mn_obj=mn_obj)
                    self.current_mn_obj = mn_obj
                    self.paint_white_rectangle_around_object(self, event, mn_obj= mn_obj)
                    self.lblXval['text'] = mn_obj.x
                    self.lblYval['text'] = mn_obj.y
                else:
                    mn_obj = self.mnemo_obj_list.head
                    # Проходим по списку объектов
                    # Если объект был выделен - снять выделение
                    while mn_obj is not None:
                        if mn_obj.key.selected_flag == 1:
                            mn_obj.key.selected_flag = 0
                            # удаляем прямоугольники, означающие выделение объектов:
                            self.canvas_with_objects.delete(self.canvas_with_objects.find_withtag('selected-'+ \
                                                                                                  mn_obj.key.obj_name))
                        mn_obj = mn_obj.next
                    self.group_selected_flag = 0
                    self.repaint_frames_around_objects(self)

    def end_drag_and_drop(self, event):
        """
        Когда кликаем левой кнопкой мыши и начинает перемещать мышь
        по Canvas, это означает, что хотим выделить сразу несколько объектов
        мнемосхемы.
        Эта функция вызывается, когда левую кнопку мыши отпустили
        """
        self.dd_x_current = self.canvas_with_objects.canvasx(event.x)
        self.dd_y_current = self.canvas_with_objects.canvasy(event.y)
        cntr = 0
        self.btn_pushed = 0
        if self.create_object == 0:
            self.canvas_with_objects.delete("selector")

            if self.mnemo_obj_list is not None:
                # если список объектов не пуст
                cur_obj = self.mnemo_obj_list.head
                while cur_obj !=None:
                    if (self.dd_x_coord_begin <= cur_obj.key.x <= self.dd_x_current) and \
                        (self.dd_x_coord_begin <= cur_obj.key.x + cur_obj.key.width <= self.dd_x_current):
                        if (self.dd_y_coord_begin <= cur_obj.key.y <= self.dd_y_current) and \
                                (self.dd_y_coord_begin <= cur_obj.key.y + cur_obj.key.height <= self.dd_y_current):
                            # объект попал в периметр выделения
                            cur_obj.key.selected_flag = 1
                            self.group_selected_flag = 1
                            cntr += 1
                    cur_obj = cur_obj.next
                self.repaint_frames_around_objects(self)

    def delete_selected_object(self, event):
        """
        Удалить выделенный объект.
        Объект может быть выделен двумя способами:
        1) с помощью клика по объекту на картинке
        2) с помощью выделения объекта в дереве объектов
        """
        if self.mnemo_obj_list is not None:
            if self.group_selected_flag == 0:
                # удаляем еденичный выделенный объект:
                if self.current_mn_obj is not None:
                    self.canvas_with_objects.delete('title-' + self.current_mn_obj.obj_title)
                    self.delete_object(self,
                                       mn_obj= self.current_mn_obj)
                    self.current_mn_obj = None
            else:
                # выделено сразу несколько объектов
                list_obj = self.mnemo_obj_list.head
                while list_obj is not None:
                    if list_obj.key.selected_flag == 1:
                        # удаляем нарисованные ранее прямоугольники:
                        self.canvas_with_objects.delete('selected-' + list_obj.key.obj_name)
                        self.canvas_with_objects.delete('title-'+ list_obj.key.obj_title)
                        self.delete_object(self,
                                           mn_obj= list_obj.key)
                    list_obj = list_obj.next
                    self.group_selected_flag = 0

    def delete_object(self, mn_obj):
        """
        функция удаления объекта
        """
        # удаляем нарисованные ранее прямоугольники:
        tag = mn_obj.type + '-' + mn_obj.obj_name
        self.canvas_with_objects.delete(tag)
        self.mnemo_obj_list.delete(self.mnemo_obj_list.search(mn_obj=mn_obj))  # удаляем объект из списка
        self.obj_tree.delete(mn_obj.obj_name) # удаляем объект из дерева объектов
        self.repaint_frames_around_objects(self)

    def save_found_contours(self):
        """
        Сохранить найденные контуры и путь к сохранённой картинке/
        Первой строкой в файле будет путь к картинке с нарисованными контурами.
        Все последующие строки - это информация о контурах:
        obj_title; pd; x; y; w; h\n
        """
        # получаем имя файла:
        filename = filedialog.asksaveasfilename(filetypes=(("txt files", "*.txt"), ("all files", "*.*")))
        self.path_to_image_with_objects = filename

        if len(self.mnemo_obj_list) == 0:
            if len(self.Md.contours_list) != 0:
                with open(filename, mode = 'w') as file:
                    file.write(self.path_to_uploaded_screenshot + '\n')
                    for index in range (len(self.Md.contours_list)):
                        str_to_write = self.Md.contours_list[index][0] + '; ' +\
                                       self.Md.contours_list[index][1] + '; ' +\
                                       str(self.Md.contours_list[index][2]) + '; ' + \
                                       str(self.Md.contours_list[index][3]) + '; ' + \
                                       str(self.Md.contours_list[index][4]) + '; ' + \
                                       str(self.Md.contours_list[index][5]) + '; ' + \
                                       str(self.Md.contours_list[index][6]) + '\n'
                        file.write(str_to_write)
                    self.write_lines_into_file(self, file= file)
                    file.close()
        else:
            with open(filename, mode='w') as file:
                file.write(self.path_to_uploaded_screenshot + '\n')
                cur_obj_list = self.mnemo_obj_list.head
                while cur_obj_list is not None:
                    str_to_write = cur_obj_list.key.obj_name + '; ' + \
                                   cur_obj_list.key.type + '; ' + \
                                   str(cur_obj_list.key.x) + '; ' + \
                                   str(cur_obj_list.key.y) + '; ' + \
                                   str(cur_obj_list.key.width) + '; ' + \
                                   str(cur_obj_list.key.height) + '; ' + \
                                   str(cur_obj_list.key.obj_title) + '\n'
                    file.write(str_to_write)
                    cur_obj_list = cur_obj_list.next
                self.write_lines_into_file(self, file= file)
                file.close()

    def write_lines_into_file(self, file):
        """
        записываем в файл горизонтальные и вертикальные линии
        """
        file.write('Lines\n')
        if self.Md.horizontal_lines != []:
            str_to_write = ''
            # записываем линии
            for index in range(len(self.Md.horizontal_lines)):
                str_to_write = str(self.Md.horizontal_lines[index][0]) + ', ' + \
                                str(self.Md.horizontal_lines[index][1]) + ', ' + \
                                str(self.Md.horizontal_lines[index][2]) + ', ' + \
                                str(self.Md.horizontal_lines[index][3]) + ', ' + \
                                str(self.Md.horizontal_lines[index][4][0]) + ', ' + \
                                str(self.Md.horizontal_lines[index][4][1]) + ', ' + \
                                str(self.Md.horizontal_lines[index][4][2]) + '\n'
                file.write(str_to_write)

            str_to_write = ''
            # записываем линии
            for index in range(len(self.Md.vertical_lines)):
                str_to_write = str(self.Md.vertical_lines[index][0]) + ', ' + \
                                str(self.Md.vertical_lines[index][1]) + ', ' + \
                                str(self.Md.vertical_lines[index][2]) + ', ' + \
                                str(self.Md.vertical_lines[index][3]) + ', ' + \
                                str(self.Md.vertical_lines[index][4][0]) + ', ' + \
                                str(self.Md.vertical_lines[index][4][1]) + ', ' + \
                                str(self.Md.vertical_lines[index][4][2]) + '\n'
                file.write(str_to_write)

    def save_changes_in_object(self, event):
        """
        Сохранить изменения в объекте мнемосхемы.
        Речь идёт о том, что объект мнемосхемы был выделен мышью,
        его свойства были отображены, а затем изменены в
        соответствующих элементах управления.
        Считываем значения элементов управления,
        переписываем свойства объекта и обновляем картинку.
        """
        new_name = self.txtObjName.get() # имя объекта
        new_obj_type = self.cmbxObjType.get() # тип объекта
        new_title = self.txtObjTitle.get() # обозначение объекта, например "К-2"

        # если список объектов не пуст:
        if self.mnemo_obj_list is not None:
            # находим элемент в списке:
            if self.group_selected_flag == 0:
                # не группу выделяем, а один объект
                # Находим объект мнемосхемы в списке:
                mn_obj_list_el = self.mnemo_obj_list.search(mn_obj=self.current_mn_obj)

                if new_name == '':
                    messagebox.showinfo('Имя объекта не может быть пустым',
                                        'Введите имя объекта')
                    return
                if new_title == '':
                    messagebox.showinfo('Описание объекта не может быть пустым',
                                        'Введите описание объекта')
                    return
                if new_obj_type == '':
                    messagebox.showinfo('Тип объекта не может быть пустым',
                                        'Выберите тип объекта из списка')
                    return

                # имя выбранного объекта отличается от введённого:
                if mn_obj_list_el.key.obj_name != new_name:
                    # сперва проверим - нет ли в списке другого объекта с таким же именем:
                    if self.mnemo_obj_list.search(obj_name=new_name) is not None:
                        # объект с таким именем уже есть
                        messagebox.showinfo('Объект с таким именем уже существует',
                                            'Введите уникальное имя объекта')
                        return
                    else:
                        if self.mnemo_obj_list.search(obj_name=new_name) is None:
                            # не найден никакой объект с таким именем -
                            # заменяем имя выбранного объекта на новое
                            mn_obj_list_el.key.obj_name = new_name
                            self.current_mn_obj.obj_name = new_name
                else:
                    # имя соответствует имени выбранного объекта
                    # найден объект мнемосхемы и это текущий объект
                    # проверяем - может бы хотим поменять описание или тип?
                    if new_title != '':
                        if mn_obj_list_el.key.obj_title != new_title:
                            # да, меняем описание объекта
                            mn_obj_list_el.key.obj_title = new_title
                            self.current_mn_obj.obj_title = new_title
                    if new_obj_type != '':
                        if mn_obj_list_el.key.type != new_obj_type:
                            # да, меняем тип объекта:
                            mn_obj_list_el.key.type = new_obj_type
                            self.current_mn_obj.type = new_obj_type
            else:
                # выделено несколько объектов мнемосхемы.
                # В таком случае мы можем менять у них только тип
                if new_obj_type != "":
                    cur_obj = self.mnemo_obj_list.head
                    self.clear_tree(self)

                    while cur_obj is not None:
                        if cur_obj.key.selected_flag == 1:
                            # объект выделен
                            if new_obj_type != "":
                                cur_obj.key.type = new_obj_type # меняем только тип
                                self.canvas_with_objects.delete(
                                    self.canvas_with_objects.find_withtag('selected-' + \
                                    cur_obj.key.obj_name)
                                )
                        self.insert_obj_into_tree(self, cur_obj.key)
                        cur_obj = cur_obj.next

                    self.repaint_frames_around_objects(self)
                    # очищаем элементы управления:
        self.txtObjName.delete(0, END)
        self.cmbxObjType.delete(0, END)
        self.txtObjTitle.delete(0, END)

    def merge_objects(self, event):
        """
        объединение группы объектов в один объект
        """
        if (self.mnemo_obj_list is not None) and (self.group_selected_flag == 1):
            new_work_list = MnemoObjList() # новый временный список для хранения выделенных объектов
            cur_obj_of_list = self.mnemo_obj_list.head

            while cur_obj_of_list is not None:
                if cur_obj_of_list.key.selected_flag == 1:
                    # объект выделен
                    new_list_el = MnemoObjList()
                    # создаём новый объект и помещаем его в список:
                    new_el = MnemoObj([
                        cur_obj_of_list.key.obj_name,
                        cur_obj_of_list.key.type,
                        cur_obj_of_list.key.x,
                        cur_obj_of_list.key.y,
                        cur_obj_of_list.key.width,
                        cur_obj_of_list.key.height,
                        cur_obj_of_list.key.obj_title
                    ])
                    new_list_el.key = new_el
                    new_work_list.insert(new_list_el) # вставляем объект во временный список
                    # удаляем нарисованные прямоугольник выделенного объекта:
                    self.canvas_with_objects.delete('selected-' + cur_obj_of_list.key.obj_name)
                    # удаляем выделенный объект из дерева объектов, списка объектов и удаляем
                    # прямоугольник вокруг объекта:
                    self.delete_object(self, mn_obj=cur_obj_of_list.key)
                cur_obj_of_list = cur_obj_of_list.next

            cur_obj_of_list = new_work_list.head
            min_x = cur_obj_of_list.key.x
            min_y = cur_obj_of_list.key.y
            max_x = cur_obj_of_list.key.x + cur_obj_of_list.key.width
            max_y = cur_obj_of_list.key.y + cur_obj_of_list.key.height
            new_type = cur_obj_of_list.key.type
            new_title = cur_obj_of_list.key.obj_title
            new_name = 'object-' + str(time.perf_counter()) # задаём уникальное имя объекта

            while cur_obj_of_list is not None:
                # определяем самый левый и самый верхний предел контуров:
                if cur_obj_of_list.key.x < min_x:
                    min_x = cur_obj_of_list.key.x
                if cur_obj_of_list.key.y < min_y:
                    min_y = cur_obj_of_list.key.y
                # определяем самый правый и самый нижний предел контуров:
                if (cur_obj_of_list.key.x + cur_obj_of_list.key.width) > max_x:
                    max_x = cur_obj_of_list.key.x + cur_obj_of_list.key.width
                if (cur_obj_of_list.key.y + cur_obj_of_list.key.height) > max_y:
                    max_y = cur_obj_of_list.key.y + cur_obj_of_list.key.height
                cur_obj_of_list = cur_obj_of_list.next

            new_work_list = None
            # создаём новый объект
            new_obj = MnemoObj([new_name,
                                new_type,
                                min_x,
                                min_y,
                                max_x - min_x,
                                max_y - min_y,
                                new_title])
            new_obj_list = MnemoObjList()
            new_obj_list.key = new_obj
            self.mnemo_obj_list.insert(new_obj_list) #вставляем новый объект в список объектов
            self.insert_obj_into_tree(self, mn_obj=new_obj_list.key)
            self.repaint_frames_around_objects(self)
            self.group_selected_flag = 0
            self.btn_pushed = 0

    def open_found_contours(self):
        """
        Загрузить картинку с сохранёнными ранее контурами,
        а также перечень контуров
        """
        if self.path_to_image_with_objects == "":
            filename = filedialog.askopenfilename(filetypes=(("txt files", "*.txt"), ("all files", "*.*")))
        else:
            filename = self.path_to_image_with_objects
            self.path_to_image_with_objects = ""

        if filename != '':
            with open(filename, mode='r') as file:
                file_rows = file.readlines()

                self.path_to_uploaded_screenshot = file_rows[0].rstrip('\n') # считываем путь к картинке с контурами
                self.upload_screenshot(self, file = self.path_to_uploaded_screenshot) # выводим на экран картинку с найденными контурами
                self.window.title('Автомнемо - ' + self.path_to_uploaded_screenshot)

                index = 1
                while index < len(file_rows):
                    if file_rows[index] != 'Lines\n':
                        obj_str = file_rows[index].rstrip('\n').split('; ')
                        mn_list_el = MnemoObjList()  # новый элемент списка
                        mn_list_el.key = MnemoObj(obj_str) # создаём новый объект
                        self.mnemo_obj_list.insert(mn_list_el)  # вставляем объект в список
                    else:
                        jindex = index+1
                        while jindex < len(file_rows):
                            line_info = file_rows[jindex].rstrip('\n').split(', ')
                            mn_line_el = MnemoObjList()

                            color_title = 'black'
                            color = [int(line_info[4]), int(line_info[5]), int(line_info[6])]

                            for index in range(len(self.Md.lines_colors)):
                                if (self.Md.lines_colors[index][0] == color[0]) and \
                                    (self.Md.lines_colors[index][1] == color[1]) and \
                                    (self.Md.lines_colors[index][2] == color[2]):
                                    # цвет найден - получаем название цвета
                                    color_title = self.Md.lines_colors[index][3]

                            # создаём линию:
                            mn_line_el.key = MnemoLineObj(line_info=line_info, color_title= color_title)
                            self.mnemo_lines_list.insert(mn_line_el)
                            jindex += 1
                        break
                    index += 1

                file.close()

            cur_obj_list = self.mnemo_obj_list.head
            while cur_obj_list is not None:
                self.insert_obj_into_tree(self, mn_obj= cur_obj_list.key)  # вставляем объект в дерево объектов
                cur_obj_list = cur_obj_list.next

            self.repaint_frames_around_objects(self)

    def create_new_object(self, event):
        """
        создание нового объекта мнемосхемы
        """
        if self.create_object == 0:
            # начинаем создавать новый объект
            self.create_object = 1 # выставляем
            # очищаем элементы управления:
            self.txtNewObjName.delete(0, END)
            self.cmbxNewObjType.delete(0, END)
            self.txtNewObjTitle.delete(0, END)
            # Имя объекта (уникально):
            self.txtNewObjName.insert(0, 'object-'+str(time.perf_counter()))
            self.btnCreateObj['text'] = 'Завершить создание объекта'
        else:
            # завершаем создание нового объекта
            self.create_object = 0
            self.btnCreateObj['text'] = 'Создать объект'
            new_obj_name = self.txtNewObjName.get()
            new_obj_type = self.cmbxNewObjType.get()
            new_obj_title = self.txtNewObjTitle.get()
            if new_obj_name == "":
                messagebox.showinfo("Имя объекта не может быть пустым",
                                    "Введите имя нового объекта")
                return
            else:
                if self.mnemo_obj_list.search(obj_name=new_obj_name) is not None:
                    messagebox.showinfo("Имя объекта должно быть уникальным",
                                        "Введите уникальное имя объекта")
                    return
            if new_obj_title == "":
                messagebox.showinfo("Обозначение объекта не может быть пустым",
                                    "Введите обозначение нового объекта")
                return
            else:
                if self.mnemo_obj_list.search(obj_title=new_obj_title) is not None:
                    messagebox.showinfo("Обозначение объекта должно быть уникальным",
                                        "Введите уникальное обозначение объекта")
                    return

            if new_obj_type == "":
                messagebox.showinfo("Не выбран тип объекта",
                                    "Выберите тип объекта из списка")
                return

            new_mn_obj = MnemoObj([
                new_obj_name,
                new_obj_type,
                self.dd_x_coord_begin,
                self.dd_y_coord_begin,
                self.dd_x_current - self.dd_x_coord_begin,
                self.dd_y_current - self.dd_y_coord_begin,
                new_obj_title
            ])
            # очищаем элементы управления:
            self.txtNewObjName.delete(0, END)
            self.cmbxNewObjType.delete(0, END)
            self.txtNewObjTitle.delete(0, END)

            new_mn_obj_lst = MnemoObjList()
            new_mn_obj_lst.key = new_mn_obj
            self.mnemo_obj_list.insert(new_mn_obj_lst) # вставляем объект
            self.insert_obj_into_tree(self, mn_obj=new_mn_obj_lst.key) # вставляем объект в дерево
            self.repaint_frames_around_objects(self)

    def generate_svg_file(self):
        """
        сгенерировать файл SVG из обнаруженных объектов мнемосхемы
        """
        if self.mnemo_obj_list is not None:
            svg_builder = SVGBuilder(self.canvas_with_objects['width'],
                                     self.canvas_with_objects['height'],
                                     self.mnemo_obj_list,
                                     self.mnemo_lines_list)
            svg_builder.build_svg()
            svg_builder.write_file()
            print('SVG exported succesfully')

gui = GUI
gui.__init__(GUI)
gui.build_window(GUI)
gui.window.mainloop()