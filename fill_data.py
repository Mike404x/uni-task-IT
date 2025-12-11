import sqlite3
import random

def fill_database():
    print("Свързване с базата данни...")
    conn = sqlite3.connect("university.db")
    cur = conn.cursor()
    
    # 1. ПРЕПОДАВАТЕЛИ
    profs = [
        ("Емил Делинов", "Доцент"),
        ("Мирослав Тотев", "Професор"),
        ("Стефан Николов", "Гл. Асистент"),
        ("Елена Петрова", "Доцент"),
        ("Георги Христов", "Професор")
    ]    
    print("Добавяне на преподаватели...")
    cur.executemany("INSERT INTO professors (name, title) VALUES (?, ?)", profs)
    cur.execute("SELECT id FROM professors")
    prof_ids = [row[0] for row in cur.fetchall()]

    # 2. ДИСЦИПЛИНИ
    courses = [
        ("Бази от Данни", random.choice(prof_ids)),
        ("Програмиране на Python", random.choice(prof_ids)),
        ("Обектно-Ориентирано Програмиране", random.choice(prof_ids)),
        ("Компютърни Мрежи", random.choice(prof_ids)),
        ("Уеб Дизайн", random.choice(prof_ids)),
        ("Алгоритми и Структури", random.choice(prof_ids)),
        ("Изкуствен Интелект", random.choice(prof_ids)),
        ("Информационни системи", random.choice(prof_ids))
    ]
    print("Добавяне на дисциплини...")
    cur.executemany("INSERT INTO courses (name, professor_id) VALUES (?, ?)", courses)
    cur.execute("SELECT id FROM courses")
    course_ids = [row[0] for row in cur.fetchall()]

    # 3. СТУДЕНТИ
    students = [
        ("Михаил Христов", "100", "Софтуерно Инж."),
        ("Александър Томов", "101", "КСТ"),
        ("Боряна Илиева", "102", "ИИТ"),
        ("Васил Василев", "103", "КСТ"),
        ("Габриела Митева", "104", "Софтуерно Инж."),
        ("Димитър Пенев", "105", "КСТ"),
        ("Емилия Йорданова", "106", "ИИТ"),
        ("Живко Стоянов", "107", "Софтуерно Инж."),
        ("Златина Колева", "108", "КСТ"),
        ("Ивайло Маринов", "109", "ИИТ"),
        ("Катерина Добрева", "110", "Софтуерно Инж.")
    ]
    
    print("Добавяне на студенти...")
    # Използваме INSERT OR IGNORE, за да не гърми, ако пуснеш скрипта два пъти
    cur.executemany("INSERT OR IGNORE INTO students (name, fn, major) VALUES (?, ?, ?)", students)
    cur.execute("SELECT id FROM students")
    student_ids = [row[0] for row in cur.fetchall()]

    # 4. ОЦЕНКИ
    print("Генериране на случайни оценки...")
    grades = []
    for s_id in student_ids:
        num_grades = random.randint(3, 5)
        taken_courses = random.sample(course_ids, num_grades)
        
        for c_id in taken_courses:
            grade = round(random.uniform(3.00, 6.00), 2)
            grades.append((s_id, c_id, grade))

    cur.executemany("INSERT INTO grades (student_id, course_id, grade) VALUES (?, ?, ?)", grades)
    conn.commit()
    conn.close()
    print("\nБазата данни е пълна с информация.")
    print("Сега стартирай главното приложение и виж резултата.")

if __name__ == "__main__":
    fill_database()