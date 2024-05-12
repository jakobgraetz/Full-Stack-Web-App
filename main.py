# All the necessary imports for main.py.
from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import requests
import json

# Initializes Flask app.
app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True


# SQLite table initialization.
# Should be handled in one *.db file!
def create_tables():
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

# Inserts the given server data into the DB.
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


# Checks if a given email is present in the database.
def is_email_in_db(email: str):
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


# Returns the user id corresponding to the given email
def get_user_id(email: str):
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
    # The server data, in form of a dict.
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


create_tables()

get_servers()

# HTTP error handlers:
# 400 Bad Request error handler
@app.errorhandler(400)
def bad_request_error(error):
    return "400 - Bad Request: Your request syntax is as messed up as a creeper explosion!"

# 401 Unauthorized error handler
@app.errorhandler(401)
def unauthorized_error(error):
    return "401 - Unauthorized: You need to login to access this area. Only players with diamond armor allowed!"

# 403 Forbidden error handler
@app.errorhandler(403)
def forbidden_error(error):
    return "403 - Forbidden: You don't have permission to access this area. The Ender Dragon guards it fiercely!"

# 404 Not Found error handler
@app.errorhandler(404)
def not_found_error(error):
    return "404 - Not Found: You stumbled upon a block that doesn't exist in this world!"

# 405 Method Not Allowed error handler
@app.errorhandler(405)
def method_not_allowed_error(error):
    return "405 - Method Not Allowed: That action isn't allowed in this realm. Check your inventory for alternative tools!"

# 406 Not Acceptable error handler
@app.errorhandler(406)
def not_acceptable_error(error):
    return "406 - Not Acceptable: The server can't generate a response that meets the requested characteristics. Like trying to craft dirt into diamonds!"

# 408 Request Timeout error handler
@app.errorhandler(408)
def request_timeout_error(error):
    return "408 - Request Timeout: The server timed out waiting for your request. Maybe you're lost in the Nether?"

# 410 Gone error handler
@app.errorhandler(410)
def gone_error(error):
    return "410 - Gone: That resource has been permanently removed from this world. Looks like it got deleted by Herobrine!"

# 500 Internal Server Error handler
@app.errorhandler(500)
def internal_server_error(error):
    return "500 - Internal Server Error: Redstone circuit malfunction! Unable to complete your request."

# 501 Not Implemented error handler
@app.errorhandler(501)
def not_implemented_error(error):
    return "501 - Not Implemented: The server doesn't support the functionality required to fulfill the request. Needs some enchantments!"

# 502 Bad Gateway error handler
@app.errorhandler(502)
def bad_gateway_error(error):
    return "502 - Bad Gateway: The server received an invalid response from the upstream server. Like trying to connect to the End from the Overworld!"

# 503 Service Unavailable error handler
@app.errorhandler(503)
def service_unavailable_error(error):
    return "503 - Service Unavailable: The server is currently unable to handle the request due to maintenance or overload. The Ender Dragon is wreaking havoc!"

# 504 Gateway Timeout error handler
@app.errorhandler(504)
def gateway_timeout_error(error):
    return "504 - Gateway Timeout: The server didn't receive a timely response from the upstream server. Looks like the End Portal is closed!"

# Custom error handler for other errors
@app.errorhandler(Exception)
def handle_error(error):
    return "500 - Internal Server Error: An unexpected glitch occurred. Steve is investigating!"

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8080)

# TODO: REMOVE UNNECESSARY PRINTS!
