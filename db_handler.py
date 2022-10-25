import sqlite3 as sq

CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS users (
user_id int PRIMARY KEY,
username text,
chat_id int,
city text,
registration_time DEFAULT CURRENT_TIMESTAMP
);
"""

CREATE_USER = """
INSERT INTO users (user_id, username, chat_id) VALUES (?, ?, ?);
"""

SELECT_USER = """
SELECT user_id, username, chat_id FROM users WHERE user_id = %s
"""


class SQLiteClient:
    def __init__(self, filepath: str) -> None:
        self.filepath = filepath
        self.conn = None

    def create_conn(self):
        self.conn = sq.connect(self.filepath, check_same_thread=False)

    def execute_query(self, command: str, params: tuple):
        if self.conn is not None:
            self.conn.execute(command, params)
            self.conn.commit()
        else:
            raise ConnectionError("No connection with database")

    def execute_select_query(self, command: str):
        if self.conn is not None:
            cur = self.conn.cursor()
            cur.execute(command)
            return cur.fetchall()
        else:
            raise ConnectionError("No connection with database")


# на базе созданного класса создадим другой класс, который отвечал бы
# за получение пользователя и за регистрацию пользователя


class UserHandler:
    SELECT_USER = """
    SELECT user_id, username, chat_id FROM users WHERE user_id = %s
    """

    CREATE_USER = """
    INSERT INTO users (user_id, username, chat_id) VALUES (?, ?, ?);
    """

    UPDATE_VALUE = """
    UPDATE users SET {}=? WHERE user_id=?;
    """

    SELECT_VALUE = """
    SELECT %s FROM users WHERE user_id=%s AND %s IS NOT NULL;"""

    def __init__(self, database_client: SQLiteClient) -> None:
        self.database_client = database_client

    def setup(self):
        self.database_client.create_conn()

    def get_user(self, user_id: str):
        user = self.database_client.execute_select_query(self.SELECT_USER % user_id)
        return user[0] if user else []

    def get_value(self, value: str, user_id: str) -> str | list:
        user = self.database_client.execute_select_query(
            self.SELECT_VALUE % (value, user_id, value))
        return user[0] if user else []

    def create_user(self, user_id: str, username: str, chat_id: int):
        # create new user
        self.database_client.execute_query(
            self.CREATE_USER, (user_id, username, chat_id)
        )

    def update_value(self, user_id: str, fieldname: str, value: str | int):
        # add value into a field named fieldname for user with user_id
        self.database_client.execute_query(
            self.UPDATE_VALUE.format(fieldname), (value, user_id)
        )

if __name__ == "__main__":
    conn = sq.connect("users.db")
    # conn.execute("DROP TABLE IF EXISTS users")
    conn.execute(CREATE_TABLE)
    user_handler = UserHandler(SQLiteClient("users.db"))
    user_handler.setup()
    # user = user_handler.get_user("1")
    # print(user)
    current_city = user_handler.get_value(
        value='city',
        user_id='439019486')
    print(current_city)
