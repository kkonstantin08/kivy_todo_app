from kivymd.app import MDApp
from kivymd.uix.dialog import MDDialog
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.pickers import MDDatePicker
from datetime import datetime
from kivymd.uix.list import TwoLineAvatarIconListItem, ILeftBodyTouch
from kivymd.uix.selectioncontrol import MDCheckbox
from kivy.utils import platform
import locale
import sqlite3


class Database:
    def __init__(self):
        self.con = sqlite3.connect('todo.db')
        self.cursor = self.con.cursor()
        self.create_task_table()

    def create_task_table(self):
        """Create tasks table"""
        self.cursor.execute(
            "CREATE TABLE IF NOT EXISTS tasks(id integer PRIMARY KEY AUTOINCREMENT, task varchar(50) NOT NULL, due_date varchar(50), completed BOOLEAN NOT NULL CHECK (completed IN (0, 1)))")
        self.con.commit()

    def create_task(self, task, due_date=None):
        """Create a task"""
        self.cursor.execute("INSERT INTO tasks(task, due_date, completed) VALUES(?, ?, ?)", (task, due_date, 0))
        self.con.commit()

        # GETTING THE LAST ENTERED ITEM SO WE CAN ADD IT TO THE TASK LIST
        created_task = self.cursor.execute("SELECT id, task, due_date FROM tasks WHERE task = ? and completed = 0", (task,)).fetchall()
        return created_task[-1]

    def get_tasks(self):
        """Get tasks"""
        uncomplete_tasks = self.cursor.execute("SELECT id, task, due_date FROM tasks WHERE completed = 0").fetchall()
        completed_tasks = self.cursor.execute("SELECT id, task, due_date FROM tasks WHERE completed = 1").fetchall()

        return completed_tasks, uncomplete_tasks

    def mark_task_as_complete(self, taskid):
        """Marking tasks as complete"""
        self.cursor.execute("UPDATE tasks SET completed=1 WHERE id=?", (taskid,))
        self.con.commit()

    def mark_task_as_incomplete(self, taskid):
        """Mark task as uncomplete"""
        self.cursor.execute("UPDATE tasks SET completed=0 WHERE id=?", (taskid,))
        self.con.commit()

        # return the text of the task
        task_text = self.cursor.execute("SELECT task FROM tasks WHERE id=?", (taskid,)).fetchall()
        return task_text[0][0]

    def delete_task(self, taskid):
        """Delete a task"""
        self.cursor.execute("DELETE FROM tasks WHERE id=?", (taskid,))
        self.con.commit()

    def close_db_connection(self):
        self.con.close()


if platform == "android":
    from android.permissions import request_permissions, Permission

    request_permissions([Permission.READ_EXTERNAL_STORAGE, Permission.WRITE_EXTERNAL_STORAGE])

# Initialize db instance
db = Database()
locale.setlocale(locale.LC_ALL, "ru_RU.utf8")


class DialogContent(MDBoxLayout):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.ids.date_text.text = str(datetime.now().strftime('%A %d %B %Y'))

    def show_date_picker(self):
        """Opens the date picker"""
        date_dialog = MDDatePicker()
        date_dialog.bind(on_save=self.on_save)
        date_dialog.open()

    def on_save(self, instance, value, date_range):
        date = value.strftime('%A %d %B %Y')
        self.ids.date_text.text = str(date)


class ListItemWithCheckbox(TwoLineAvatarIconListItem):

    def __init__(self, pk=None, **kwargs):
        super().__init__(**kwargs)
        self.pk = pk

    def mark(self, check, the_list_item):
        if check.active == True:
            the_list_item.text = '[s]' + the_list_item.text + '[/s]'
            db.mark_task_as_complete(the_list_item.pk)  # here
        else:
            the_list_item.text = str(db.mark_task_as_incomplete(the_list_item.pk))  # Here

    def delete_item(self, the_list_item):
        self.parent.remove_widget(the_list_item)
        db.delete_task(the_list_item.pk)  # Here


class LeftCheckbox(ILeftBodyTouch, MDCheckbox):
    '''Custom left container'''


class MainApp(MDApp):
    task_list_dialog = None

    def build(self):
        # Setting theme to my favorite theme
        self.theme_cls.primary_palette = "DeepPurple"

    def show_task_dialog(self):
        if not self.task_list_dialog:
            self.task_list_dialog = MDDialog(
                title="Добавить Задачу",
                type="custom",
                content_cls=DialogContent(),
            )

        self.task_list_dialog.open()

    def on_start(self):
        """Load the saved tasks and add them to the MDList widget when the application starts"""
        try:
            completed_tasks, uncomplete_tasks = db.get_tasks()

            if uncomplete_tasks != []:
                for task in uncomplete_tasks:
                    add_task = ListItemWithCheckbox(pk=task[0], text=task[1], secondary_text=task[2])
                    self.root.ids.container.add_widget(add_task)

            if completed_tasks != []:
                for task in completed_tasks:
                    add_task = ListItemWithCheckbox(pk=task[0], text='[s]' + task[1] + '[/s]', secondary_text=task[2])
                    add_task.ids.check.active = True
                    self.root.ids.container.add_widget(add_task)
        except Exception as e:
            print(e)
            pass

    def close_dialog(self, *args):
        self.task_list_dialog.dismiss()

    def add_task(self, task, task_date):
        '''Add task to the list of tasks'''

        # Add task to the db
        created_task = db.create_task(task.text, task_date)  # Here

        # return the created task details and create a list item
        self.root.ids['container'].add_widget(
            ListItemWithCheckbox(pk=created_task[0], text='[b]' + created_task[1] + '[/b]', secondary_text=created_task[2]))  # Here
        task.text = ''


if __name__ == '__main__':
    app = MainApp()
    app.run()
