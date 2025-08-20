import sqlite3
import threading
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
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        self._create_tables()
        self._initialized = True

    def _create_tables(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
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
        self.conn.commit()

    def add_message(self, message: Message):
        self.cursor.execute(
            "INSERT INTO messages (tags, nick, user, host, command, middle_params, trailing) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (message.tags, message.nick, message.user, message.host, message.command, message.middle_params, message.trailing),
        )
        message_id = self.cursor.lastrowid
        self.conn.commit()
        if not message_id:
            raise sqlite3.DatabaseError(f"Couldn't get the id of the new Message {message}")
        return message_id

    def get_message_history(self, message_id: int, context_window: int = 10):
        self.cursor.execute(
            """
            SELECT * FROM messages
            WHERE id <= ?
            ORDER BY timestamp DESC
            LIMIT ?
            """,
            (message_id, context_window),
        )
        return self.cursor.fetchall()
