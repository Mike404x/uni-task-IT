import tkinter as tk
from tkinter import messagebox
import sqlite3
import ttkbootstrap as tb 
from ttkbootstrap.constants import * # =========================================================
# 1. БАЗА ДАННИ (BACKEND)
# =========================================================
class DB:
    def __init__(self):
        # Името на базата данни
        self.conn = sqlite3.connect("university.db")
        self.conn.execute("PRAGMA foreign_keys = 1") # Активираме връзките между таблиците
        self.cur = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        # 1. СТУДЕНТИ (с поле Специалност)
        self.cur.execute("""
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                fn TEXT UNIQUE NOT NULL,
                major TEXT NOT NULL
            )
        """)
        
        # 2. ПРЕПОДАВАТЕЛИ
        self.cur.execute("""
            CREATE TABLE IF NOT EXISTS professors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                title TEXT
            )
        """)

        # 3. ДИСЦИПЛИНИ (свързани с преподавател)
        self.cur.execute("""
            CREATE TABLE IF NOT EXISTS courses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                professor_id INTEGER,
                FOREIGN KEY (professor_id) REFERENCES professors (id) ON DELETE SET NULL
            )
        """)

        # 4. ОЦЕНКИ (свързани със студент и курс, каскадно триене)
        self.cur.execute("""
            CREATE TABLE IF NOT EXISTS grades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER,
                course_id INTEGER,
                grade REAL,
                date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (student_id) REFERENCES students (id) ON DELETE CASCADE,
                FOREIGN KEY (course_id) REFERENCES courses (id) ON DELETE CASCADE
            )
        """)
        self.conn.commit()

    # --- МЕТОДИ ЗА СТУДЕНТИ ---
    def add_student(self, name, fn, major):
        try:
            self.cur.execute("INSERT INTO students (name, fn, major) VALUES (?, ?, ?)", (name, fn, major))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False # Вече има такъв факултетен номер

    def get_students(self):
        self.cur.execute("SELECT * FROM students")
        return self.cur.fetchall()

    def delete_student(self, student_id):
        # Заради ON DELETE CASCADE, оценките се трият сами
        self.cur.execute("DELETE FROM students WHERE id = ?", (student_id,))
        self.conn.commit()
    
    def get_student_gpa(self, student_id):
        self.cur.execute("SELECT AVG(grade) FROM grades WHERE student_id = ?", (student_id,))
        res = self.cur.fetchone()
        return round(res[0], 2) if res and res[0] else 0.00

    # --- МЕТОДИ ЗА ПРЕПОДАВАТЕЛИ ---
    def add_professor(self, name, title):
        self.cur.execute("INSERT INTO professors (name, title) VALUES (?, ?)", (name, title))
        self.conn.commit()

    def get_professors(self):
        self.cur.execute("SELECT * FROM professors")
        return self.cur.fetchall()

    # --- МЕТОДИ ЗА КУРСОВЕ ---
    def add_course(self, name, professor_id):
        self.cur.execute("INSERT INTO courses (name, professor_id) VALUES (?, ?)", (name, professor_id))
        self.conn.commit()

    def get_courses_visual(self):
        # Взимаме имената на професорите чрез JOIN
        query = """
            SELECT courses.id, courses.name, professors.title, professors.name
            FROM courses
            LEFT JOIN professors ON courses.professor_id = professors.id
        """
        self.cur.execute(query)
        return self.cur.fetchall()

    # --- МЕТОДИ ЗА ОЦЕНКИ ---
    def add_grade(self, student_id, course_id, grade):
        self.cur.execute("INSERT INTO grades (student_id, course_id, grade) VALUES (?, ?, ?)", 
                         (student_id, course_id, grade))
        self.conn.commit()

    def get_grades_visual(self):
        # Взимаме имената на студентите и предметите
        query = """
            SELECT grades.id, students.name, students.fn, courses.name, grades.grade
            FROM grades
            JOIN students ON grades.student_id = students.id
            JOIN courses ON grades.course_id = courses.id
        """
        self.cur.execute(query)
        return self.cur.fetchall()

# =========================================================
# 2. ГРАФИЧЕН ИНТЕРФЕЙС (GUI)
# =========================================================
class UniversityApp:
    def __init__(self, root):
        self.db = DB()
        self.root = root
        self.root.title("Университетска Система")
        self.root.geometry("1100x800")
        
        # Заглавие
        lbl = tb.Label(root, text="Академична Справка & Управление", font=("Helvetica", 20, "bold"), bootstyle="primary")
        lbl.pack(pady=15)

        # Контейнер за табове
        self.notebook = tb.Notebook(root, bootstyle="primary") 
        self.notebook.pack(pady=5, padx=15, fill='both', expand=True)

        # Създаване на страниците
        self.tab_students = tb.Frame(self.notebook)
        self.tab_profs = tb.Frame(self.notebook)
        self.tab_courses = tb.Frame(self.notebook)
        self.tab_grades = tb.Frame(self.notebook)

        self.notebook.add(self.tab_students, text="🎓 Студенти")
        self.notebook.add(self.tab_profs, text="👨‍🏫 Преподаватели")
        self.notebook.add(self.tab_courses, text="📚 Дисциплини")
        self.notebook.add(self.tab_grades, text="📝 Оценки")

        # Речници за ID-та (Helper maps)
        self.map_students = {}
        self.map_profs = {}
        self.map_courses = {}

        # Стартиране на логиката за всеки таб
        self.setup_students()
        self.setup_profs()
        self.setup_courses()
        self.setup_grades()

        # Слушател за смяна на таб (Refresh)
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_change)

    # -----------------------------------------------------
    # ТАБ 1: СТУДЕНТИ (С ПОЛЕ ЗА СПЕЦИАЛНОСТ)
    # -----------------------------------------------------
    def setup_students(self):
        frame = tb.Labelframe(self.tab_students, text=" Регистрация на нов студент ", bootstyle="info")
        frame.pack(fill="x", padx=10, pady=10)

        # Използваме Grid за по-добра подредба на 3 полета
        tb.Label(frame, text="Име:").grid(row=0, column=0, padx=10, pady=15)
        self.ent_s_name = tb.Entry(frame, width=25)
        self.ent_s_name.grid(row=0, column=1, padx=10, pady=15)
        
        tb.Label(frame, text="Фак. №:").grid(row=0, column=2, padx=10, pady=15)
        self.ent_s_fn = tb.Entry(frame, width=15)
        self.ent_s_fn.grid(row=0, column=3, padx=10, pady=15)
        
        tb.Label(frame, text="Специалност:").grid(row=0, column=4, padx=10, pady=15)
        self.ent_s_major = tb.Entry(frame, width=20)
        self.ent_s_major.grid(row=0, column=5, padx=10, pady=15)

        tb.Button(frame, text="Добави", bootstyle="success", command=self.add_student).grid(row=0, column=6, padx=20, pady=15)

        # Таблица
        cols = ("ID", "Име", "Фак. №", "Специалност")
        self.tree_s = tb.Treeview(self.tab_students, columns=cols, show="headings", bootstyle="info")
        for c in cols: self.tree_s.heading(c, text=c)
        self.tree_s.column("ID", width=50)
        self.tree_s.pack(fill="both", expand=True, padx=10)

        # Бутони за действия
        btn_box = tb.Frame(self.tab_students)
        btn_box.pack(pady=10)
        tb.Button(btn_box, text="Изтрий избран", bootstyle="danger", command=self.del_student).pack(side="left", padx=5)
        tb.Button(btn_box, text="Справка Успех (GPA)", bootstyle="warning", command=self.show_gpa).pack(side="left", padx=5)

    def add_student(self):
        name = self.ent_s_name.get()
        fn = self.ent_s_fn.get()
        major = self.ent_s_major.get() # Взимаме и специалността

        if name and fn and major:
            if self.db.add_student(name, fn, major):
                self.refresh_students()
                # Чистим полетата
                self.ent_s_name.delete(0, tk.END)
                self.ent_s_fn.delete(0, tk.END)
                self.ent_s_major.delete(0, tk.END)
                messagebox.showinfo("Успех", "Студентът е добавен!")
            else: 
                messagebox.showerror("Грешка", "Дублиран Фак. номер!")
        else:
            messagebox.showwarning("Внимание", "Попълнете всички полета (Име, ФН, Специалност).")

    def del_student(self):
        sel = self.tree_s.selection()
        if sel:
            sid = self.tree_s.item(sel)['values'][0]
            if messagebox.askyesno("Сигурни ли сте?", "Това ще изтрие студента и всички негови оценки!"):
                self.db.delete_student(sid)
                self.refresh_students()
                # Трябва да обновим и таблицата с оценките, ако е отворена
                self.refresh_grades() 

    def show_gpa(self):
        sel = self.tree_s.selection()
        if sel:
            item = self.tree_s.item(sel)['values']
            gpa = self.db.get_student_gpa(item[0])
            messagebox.showinfo("Справка", f"Студент: {item[1]}\nСпециалност: {item[3]}\n\nСРЕДЕН УСПЕХ: {gpa}")
        else:
            messagebox.showwarning("Внимание", "Моля изберете студент от списъка.")

    def refresh_students(self):
        for i in self.tree_s.get_children(): self.tree_s.delete(i)
        for row in self.db.get_students(): self.tree_s.insert("", tk.END, values=row)

    # -----------------------------------------------------
    # ТАБ 2: ПРЕПОДАВАТЕЛИ
    # -----------------------------------------------------
    def setup_profs(self):
        frame = tb.Labelframe(self.tab_profs, text=" Преподавател ", bootstyle="primary")
        frame.pack(fill="x", padx=10, pady=10)

        tb.Label(frame, text="Титла (Доц./Проф.):").pack(side="left", padx=5)
        self.en_p_title = tb.Entry(frame, width=10); self.en_p_title.pack(side="left")

        tb.Label(frame, text="Име:").pack(side="left", padx=5)
        self.en_p_name = tb.Entry(frame, width=30); self.en_p_name.pack(side="left")

        tb.Button(frame, text="Добави Преподавател", bootstyle="primary", command=self.add_prof).pack(side="right", padx=10)

        cols = ("ID", "Име", "Титла")
        self.tree_p = tb.Treeview(self.tab_profs, columns=cols, show="headings", bootstyle="primary")
        for c in cols: self.tree_p.heading(c, text=c)
        self.tree_p.pack(fill="both", expand=True, padx=10, pady=5)

    def add_prof(self):
        if self.en_p_name.get():
            self.db.add_professor(self.en_p_name.get(), self.en_p_title.get())
            self.refresh_profs()
            self.en_p_name.delete(0, tk.END)

    def refresh_profs(self):
        for i in self.tree_p.get_children(): self.tree_p.delete(i)
        for row in self.db.get_professors(): self.tree_p.insert("", tk.END, values=row)

    # -----------------------------------------------------
    # ТАБ 3: ДИСЦИПЛИНИ
    # -----------------------------------------------------
    def setup_courses(self):
        frame = tb.Labelframe(self.tab_courses, text=" Нова Дисциплина ", bootstyle="secondary")
        frame.pack(fill="x", padx=10, pady=10)

        tb.Label(frame, text="Предмет:").pack(side="left", padx=5)
        self.en_c_name = tb.Entry(frame, width=25); self.en_c_name.pack(side="left")

        tb.Label(frame, text="Водещ:").pack(side="left", padx=5)
        self.cb_c_prof = tb.Combobox(frame, state="readonly", width=30)
        self.cb_c_prof.pack(side="left")

        tb.Button(frame, text="Създай", bootstyle="secondary", command=self.add_course).pack(side="right", padx=10)

        cols = ("ID", "Предмет", "Преподавател")
        self.tree_c = tb.Treeview(self.tab_courses, columns=cols, show="headings")
        self.tree_c.heading("ID", text="ID")
        self.tree_c.heading("Предмет", text="Предмет")
        self.tree_c.heading("Преподавател", text="Преподавател")
        self.tree_c.pack(fill="both", expand=True, padx=10, pady=5)

    def add_course(self):
        p_name = self.cb_c_prof.get()
        c_name = self.en_c_name.get()
        if p_name and c_name:
            pid = self.map_profs[p_name]
            self.db.add_course(c_name, pid)
            self.refresh_courses()
            self.en_c_name.delete(0, tk.END)
        else:
            messagebox.showwarning("Внимание", "Изберете име и преподавател.")

    def refresh_courses(self):
        for i in self.tree_c.get_children(): self.tree_c.delete(i)
        for row in self.db.get_courses_visual():
            # row = (id, course_name, prof_title, prof_name)
            full_prof = f"{row[2]} {row[3]}" if row[3] else "Без преподавател"
            self.tree_c.insert("", tk.END, values=(row[0], row[1], full_prof))

    # -----------------------------------------------------
    # ТАБ 4: ОЦЕНКИ
    # -----------------------------------------------------
    def setup_grades(self):
        frame = tb.Labelframe(self.tab_grades, text=" Протокол за изпит ", bootstyle="danger")
        frame.pack(fill="x", padx=10, pady=10)

        tb.Label(frame, text="Студент:").pack(side="left", padx=5)
        self.cb_g_student = tb.Combobox(frame, state="readonly", width=25)
        self.cb_g_student.pack(side="left", padx=5)
        
        tb.Label(frame, text="Дисциплина:").pack(side="left", padx=5)
        self.cb_g_course = tb.Combobox(frame, state="readonly", width=25)
        self.cb_g_course.pack(side="left", padx=5)

        tb.Label(frame, text="Оценка:").pack(side="left", padx=5)
        self.en_g_val = tb.Entry(frame, width=5)
        self.en_g_val.pack(side="left", padx=5)

        tb.Button(frame, text="Впиши", bootstyle="danger", command=self.add_grade).pack(side="left", padx=10)

        cols = ("ID", "Студент", "ФН", "Предмет", "Оценка")
        self.tree_g = tb.Treeview(self.tab_grades, columns=cols, show="headings", bootstyle="danger")
        for c in cols: self.tree_g.heading(c, text=c)
        self.tree_g.pack(fill="both", expand=True, padx=10, pady=5)

    def add_grade(self):
        s_txt = self.cb_g_student.get()
        c_txt = self.cb_g_course.get()
        try:
            val_str = self.en_g_val.get()
            if not val_str: 
                messagebox.showwarning("Внимание", "Въведете оценка.")
                return
            
            val = float(val_str)
            if s_txt and c_txt and 2 <= val <= 6:
                sid = self.map_students[s_txt]
                cid = self.map_courses[c_txt]
                self.db.add_grade(sid, cid, val)
                self.refresh_grades()
                messagebox.showinfo("Успех", "Оценката е записана!")
            else: 
                messagebox.showerror("Грешка", "Проверете данните. Оценката трябва да е между 2 и 6.")
        except ValueError: 
            messagebox.showerror("Грешка", "Оценката трябва да е число (напр. 5.50).")

    def refresh_grades(self):
        for i in self.tree_g.get_children(): self.tree_g.delete(i)
        for row in self.db.get_grades_visual():
            self.tree_g.insert("", tk.END, values=row)

    # -----------------------------------------------------
    # ОБЩА ЛОГИКА (Refresh Maps)
    # -----------------------------------------------------
    def on_tab_change(self, event):
        # 1. Зареждане на мап за Студенти
        self.map_students = {}
        s_list = []
        for s in self.db.get_students():
            txt = f"{s[1]} (ФН:{s[2]})"
            self.map_students[txt] = s[0]
            s_list.append(txt)
        self.cb_g_student['values'] = s_list

        # 2. Зареждане на мап за Преподаватели
        self.map_profs = {}
        p_list = []
        for p in self.db.get_professors():
            txt = f"{p[2]} {p[1]}" # Титла + Име
            self.map_profs[txt] = p[0]
            p_list.append(txt)
        self.cb_c_prof['values'] = p_list

        # 3. Зареждане на мап за Курсове
        self.map_courses = {}
        c_list = []
        courses = self.db.get_courses_visual() 
        for c in courses:
            txt = c[1] # Име на предмет
            self.map_courses[txt] = c[0] # ID
            c_list.append(txt)
        self.cb_g_course['values'] = c_list
        
        # Обновяване на всички таблици
        self.refresh_students()
        self.refresh_profs()
        self.refresh_courses()
        self.refresh_grades()

if __name__ == "__main__":
    app_window = tb.Window(themename="superhero") 
    app = UniversityApp(app_window)
    app_window.mainloop()