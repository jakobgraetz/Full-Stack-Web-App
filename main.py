# All the necessary imports for main.py.
from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import requests
import json

# Initializes Flask app.
app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True


def create_table():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT,
            password TEXT
        )
    """)

    conn.commit()
    conn.close()


def create_server_table():
    conn = sqlite3.connect("servers.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS servers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner INTEGER,
            server_data TEXT
        )
    """)

    conn.commit()
    conn.close()


def insert_server(owner, server_data):
    conn = sqlite3.connect("servers.db")
    cursor = conn.cursor()

    cursor.execute("INSERT INTO servers (owner, server_data) VALUES (?, ?)", (owner, server_data))

    conn.commit()
    conn.close()


def get_servers():
    conn = sqlite3.connect("servers.db")
    cursor = conn.cursor()

    cursor.execute("SELECT server_data FROM servers")
    results = cursor.fetchall()

    servers = []

    for result in results:
        json_data = result[0]
        print(json_data)
        dict_data = json.loads(json_data)
        servers.append(dict_data)

    index = 1

    servers.sort(key=lambda server: server["Players"])
    servers.reverse()
    for server in servers:
        if server["Rank"] is None:
            server["Rank"] = index
            index += 1

    conn.close()
    print(servers)
    return servers


def insert_user(email, password):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    
    cursor.execute("INSERT INTO users (email, password) VALUES (?, ?)", (email, password))
    
    conn.commit()
    conn.close()


def get_my_servers(user_id):
    conn = sqlite3.connect("servers.db")
    cursor = conn.cursor()

    cursor.execute("SELECT server_data FROM servers WHERE owner = ?", (user_id,))
    results = cursor.fetchall()

    servers = []

    for result in results:
        json_data = result[0]
        print(json_data)
        dict_data = json.loads(json_data)
        servers.append(dict_data)

    index = 1

    servers.sort(key=lambda server: server["Players"])
    servers.reverse()
    for server in servers:
        server["Rank"] = index
        index += 1

    conn.close()
    print(servers)
    return servers


def is_email_in_db(email):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    cursor.execute("SELECT email FROM users WHERE email = ?", (email,))
    result = cursor.fetchone()

    conn.close()

    return result is not None


def get_users():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()

    conn.close()
    print(users)
    return users


def get_user_id(email):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
    user_id = cursor.fetchone()

    conn.close()
    print(user_id)
    return user_id[0] if user_id else None


def check_login(email, password):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    cursor.execute("SELECT email, password FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()
    if user and user[1] == password:
        print("Login successful")
        user_id = get_user_id(email)
        session["login"] = str(user_id)
        print(f"Session['login']" + session["login"])
        return redirect(url_for("index"))
    else:
        print("Login failed")

    conn.close()


# This could definitely be handled *a lot* smoother!
def construct_new_server_dict(name, description, ip):
    players_endpoint = "https://eu.mc-api.net/v3/server/ping/" + ip
    try:
        response = requests.get(players_endpoint)
        if response.status_code == 200:
            player_data = response.json()
            if player_data.get("online", False):
                max_players = player_data.get("players", {}).get("max", 0)
                print(f"Max players: {max_players}")
                online_players = player_data.get("players", {}).get("online", 0)
                print(f"Online players: {online_players}")
            else:
                print("Server is offline.")
        else:
            print(f"Error: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
    server_dict = {
        "Rank": None,
        "Name": name,
        "Server": description,
        "Players": max_players,
        "IP": ip
    }
    return server_dict


@app.route("/")
def index():
    return render_template("index.html", servers=get_servers())


@app.route("/sponsor")
def sponsored():
    return "sponsor this website to increase your traffic! coming soon!"


@app.route("/servers")
def server_list():
    server_list = get_servers()
    return server_list


@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if "login" not in session:
        return redirect(url_for("login"))
    user_id = session["login"]
    if request.method == "POST":
        server_name = request.form.get("server-name")
        server_description = request.form.get("server-description")
        server_address = request.form.get("address")
        # https://mc-api.net/docs/ping
        print(server_name)
        print(server_description)
        print(server_address)
        owner = session["login"]
        server_dict = construct_new_server_dict(server_name, server_description, server_address)
        serialized_server_dict = json.dumps(server_dict)
        insert_server(owner, serialized_server_dict)
        print(server_dict)

        return redirect(url_for("dashboard"))
    return render_template("dashboard.html", servers=get_my_servers(user_id))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        print(f"E-Mail is: " + email)
        password = request.form.get("password")
        print(f"Password is: " + password)
        check_login(email, password)
        return redirect(url_for("index"))
    return render_template("login.html", servers=get_servers())


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        email = request.form.get("email")
        print(f"E-Mail is: " + email)
        password = request.form.get("password")
        print(f"Password is: " + password)
        if is_email_in_db(email):
            print("Email already in database!")
            print("Attempting Login!")
            check_login(email, password)
            return redirect(url_for("index"))
        else:
            insert_user(email, password)
            print("Registered New User!")
            return redirect(url_for("index"))
        return render_template("login.html", servers=get_servers())
    return render_template("signup.html", servers=get_servers())


@app.route("/logout", methods=["GET", "POST"])
def logout():
    session.pop("login", None)
    return redirect(url_for("index"))


create_table()
create_server_table()

get_servers()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8080)


# TODO: ERROR HANDLERS!

# TODO: REMOVE UNNECESSARY PRINTS!