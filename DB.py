import sqlite3
import threading
import queue
from Message import Message

class Database:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, db_path: str = "chat.db"):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(Database, cls).__new__(cls)
                cls._instance._initialized = False
        return cls._instance

    def __init__(self, db_path: str = "chat.db"):
        if self._initialized:
            return
        self.write_conn = sqlite3.connect(db_path, check_same_thread=False)
        self.write_conn.row_factory = sqlite3.Row
        self.write_cursor = self.write_conn.cursor()

        self.read_conn = sqlite3.connect(db_path, check_same_thread=False)
        self.read_conn.row_factory = sqlite3.Row
        self.read_cursor = self.read_conn.cursor()
        self.read_lock = threading.Lock()

        self._create_tables()

        self.write_queue = queue.Queue()
        self.running = True
        self.worker = threading.Thread(target=self._process_writes, daemon=True)
        self.worker.start()

        self._initialized = True

    def _create_tables(self):
        self.write_cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                full_text TEXT,
                tags TEXT,
                nick TEXT,
                user TEXT,
                host TEXT,
                command TEXT,
                middle_params TEXT,
                trailing TEXT
            )
        """)

        # self.cursor.execute("""
        #     CREATE TABLE IF NOT EXISTS tasks (
        #         id INTEGER PRIMARY KEY AUTOINCREMENT,
        #         message_id INTEGER NOT NULL,
        #         task_type TEXT NOT NULL DEFAULT 'generate_response',
        #         created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        #         FOREIGN KEY (message_id) REFERENCES messages(id)
        #     )
        # """)
        #
        self.write_conn.commit()

    def _process_writes(self):
        while self.running:
            try:
                func, args, kwargs = self.write_queue.get(timeout=1)
                func(*args, **kwargs)
                self.write_conn.commit()
                self.write_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                print(e)

    def add_message(self, message: Message):
        def _insert(msg: Message):
            self.write_cursor.execute(
                "INSERT INTO messages (full_text, tags, nick, user, host, command, middle_params, trailing) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (msg.full_text, msg.tags, msg.nick, msg.user, msg.host, msg.command,
                 msg.middle_params, msg.trailing),
            )

        self.write_queue.put((_insert, (message,), {}))

    def get_message_history(self, context_window: int = 10):
        allowed_commands = {"JOIN", "PRIVMSG", "421", "366", "353", "001"}
        with self.read_lock:
            self.read_cursor.execute(
                """
                SELECT * FROM messages
                WHERE 
                    (command GLOB '*[A-Z]*')
                    OR
                    command IN ({})
                ORDER BY timestamp DESC
                LIMIT ?
                """.format(",".join("?" * len(allowed_commands))),
                (*allowed_commands, context_window),
            )
            rows = self.read_cursor.fetchall()
            messages = []
            for row in rows:
                msg = Message(
                    full_text=row["full_text"],
                    tags=row["tags"],
                    nick=row["nick"],
                    user=row["user"],
                    host=row["host"],
                    command=row["command"],
                    middle_params=row["middle_params"],
                    trailing=row["trailing"]
                )
                messages.append(msg)
            return messages

    def stop(self):
        self.running = False
        self.worker.join(timeout=2)
        self.write_conn.close()
        self.read_conn.close()
