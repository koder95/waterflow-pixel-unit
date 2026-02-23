from phew import server, connect_to_wifi, access_point, logging
from network import hostname
import uasyncio
import machine
import json
import config
from waterflowdriver import WaterflowDriver

def load_json(filename):
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except:
        logging.debug(f'Cannot read: {filename}')
        return { }

def save_json(filename, content):
    try:
        with open(filename, 'w') as f:
            json.dump(content, f)
            return True
    except:
        logging.debug(f'Cannot write {content} into {filename}')
        return False

net = load_json('net.json')
driver = WaterflowDriver()
name = config.device['application-name']
hostname(name)
ip = connect_to_wifi(net['ssid'], net['pass'])
if (ip is None):
    ip = access_point(net['ap-ssid'], net['ap-pass'])
    print('AP IP', ip)
    logging.info(f'> {name} – uruchomiono AP: IP ({ip})')
else:
    print('IP', ip)
    logging.info(f'> {name} – połączenie z siecią: IP ({ip})')
    import ntptime
    ntptime.settime()

def generate_token():
    import ubinascii
    import random
    r = bytearray(random.randbytes(32))
    rhex = ubinascii.hexlify(r)
    return ubinascii.b2a_base64(rhex).strip()

def refresh_token(username):
    users = load_json('users.json')
    if (username in users):
        users[username]['token'] = generate_token()
        if (save_json('users.json', users)):
            logging.info(f'> refresh token for {username}')
            return {"token": users[username]['token'], "user": username}
        else:
            logging.debug(f'> cannot refresh token for {username}')
            return {'message': 'Cannot generate access token. Try again.'}
    else:
        return {'message': f'User {username} not exists'}

def load_logs():
    filename = logging.log_file
    try:
        with open(filename, 'r') as f:
            return f.read()
    except:
        logging.debug(f'Cannot read: {filename}')
        return { }
    

@server.route("/api/info", methods=["GET"])
def get_device_info(request):
    return json.dumps(config.device), 200, {"Content-type": "application/json"}

@server.route("/api/logs", methods=["GET"])
def get_logs(request):
    content = load_logs()
    lines = content.split("\n")
    return json.dumps(lines), 200, {"Content-type": "application/json"}    

@server.route("/api/restart", methods=["POST"])
def restart(request):
    logging.info('> restarting by http request')
    restartCountdown = 10
    if ("defaultRestartCountdown" in driver.data):
        restartCountdown = driver.data["defaultRestartCountdown"]
    driver.restartCountdown = restartCountdown
    return json.dumps({"restartCountdown": restartCountdown}), 200, {"Content-type": "application/json"}

@server.route("/api/secure/admin/reset", methods=["POST"])
def reset_admin_pass(request):
    if ('secure' in request.headers):
        if (request.headers['secure'] == config.secured['secure']):
            users = load_json('users.json')
            if ('pass' in request.data):
                users['admin']['pass'] = request.data['pass']
                if (len(users['admin']['pass']) > 6):
                    if (save_json('users.json', users)):
                        return json.dumps({"message": "Password was changed successfully."}), 202, {"Content-type": "application/json"}
                    else:
                        return json.dumps({"message": "Password was not changed. Cannot rewrite file!"}), 500, {"Content-type": "application/json"}
                else:
                    return json.dumps({"message": "Password was not changed. New password must restrict password rules."}), 406, {"Content-type": "application/json"}
            else:
                return json.dumps({"message": "Password was not changed. Enter new password."}), 400, {"Content-type": "application/json"}
        else:
            return json.dumps({"message": "Password was not changed. Access denied."}), 401, {"Content-type": "application/json"}
    else:
        return json.dumps({"message": "Password was not changed. Special key is required."}), 401, {"Content-type": "application/json"}
                

@server.route("/api/secure/access", methods=["POST"])
def user_access(request):
    if ('user' in request.headers):
        username = request.headers['user']
        if ('pass' in request.headers):
            password = request.headers['pass']
            users = load_json('users.json')
            if (username in users):
                if (password == users[username]['pass']):
                    users[username]['token'] = generate_token()
                    if (save_json('users.json', users)):
                        logging.info(f'> new access token generated for {username}')
                        return json.dumps({"token": users[username]['token'], "user": username}), 200, {"Content-type": "application/json"}
                    else:
                        logging.info(f'> cannot generate access token for {username} – saving problems')
                        return json.dumps({'message': 'Cannot generate access token. Try again.'}), 500, {"Content-type": "application/json"}
            return json.dumps({'message': f'User "{username}" not exists or password is incorrect'}), 401, {"Content-type": "application/json"}
        return json.dumps({'message': 'Enter a password'}), 401, {"Content-type": "application/json"}
    return json.dumps({'message': 'Enter a username'}), 401, {"Content-type": "application/json"}

@server.route("/api/secure/pass", methods=["PATCH"])
def user_pass_change(request):
    if ('user' in request.headers):
        username = request.headers['user']
        if ('token' in request.headers):
            token = request.headers['token']
            users = load_json('users.json')
            if (username in users):
                if (token == users[username]['token']):
                    if ('pass' in request.data):
                        users[username]['pass'] = request.data['pass']
                        if (users[username]['pass'] > 6):
                            if (save_json('users.json', users)):
                                return json.dumps({}), 202, {"Content-type": "application/json"}
                            else:
                                logging.info(f'> cannot change password for {username} – saving problems')
                                return json.dumps({'message': 'Cannot change password. Try again.'}), 500, {"Content-type": "application/json"}
                        return json.dumps({"message": "Password was not changed. New password must restrict password rules."}), 406, {"Content-type": "application/json"}
                    return json.dumps({"message": "Password was not changed. Enter new password."}), 400, {"Content-type": "application/json"}
            return json.dumps({'message': f'User "{username}" not exists or token is incorrect'}), 401, {"Content-type": "application/json"}
        return json.dumps({'message': 'Enter a token'}), 401, {"Content-type": "application/json"}
    return json.dumps({'message': 'Enter a username'}), 401, {"Content-type": "application/json"}

@server.route("/api/secure/app", methods=["POST"])
def app_access(request):
    return json.dumps({}), 501, {"Content-type": "application/json"}
    
@server.route("/api/secure/data", methods=["PUT", "PATCH"])
def change_data(request):
    if ('user' in request.headers):
        user = request.headers['user']
        if ('token' in request.headers):
            accessToken = request.headers['token']
            users = load_json('users.json')
            if (user in users):
                if (accessToken == users[user]['token']):
                    old = load_json('data.json')
                    data = request.data
                    if ('nol' not in data):
                        data['nol'] = 3
                    if (request.method == "PUT"):
                        if (save_json('data.json', data)):
                            new_credentials = refresh_token(user)
                            return json.dumps({'old': old, 'new': data, 'newCredentials': new_credentials}), 202, {"Content-type": "application/json"}
                        else:
                            return json.dumps({'message': 'Cannot save', 'data': data}), 500, {"Content-type": "application/json"}
                    else:
                        new = old.copy()
                        new.update(data)
                        if (save_json('data.json', new)):
                            new_credentials = refresh_token(user)
                            return json.dumps({'old': old, 'new': new, 'newCredentials': new_credentials}), 202, {"Content-type": "application/json"}
                        else:
                            return json.dumps({'message': 'Cannot save', 'data': data}), 500, {"Content-type": "application/json"}
    return json.dumps({}), 401, {"Content-type": "application/json"}

@server.route("/api/secure/admin", methods=["GET"])
def get_secure(request):
    if ('user' in request.headers):
        user = request.headers['user']
        if ('token' in request.headers):
            accessToken = request.headers['token']
            users = load_json('users.json')
            if (user in users):
                if (accessToken == users[user]['token']):
                    return json.dumps(config.secured), 200, {"Content-type": "application/json"}
    return json.dumps({}), 401, {"Content-type": "application/json"}
    
@server.route("/api/wifi", methods=["PATCH"])
def wifi_conf(request):
    old = load_json('net.json')
    new = old.copy()
    new.update(request.data)
    accepted = old.copy()
    accepted['ssid'] = new['ssid']
    accepted['pass'] = new['pass']
    accepted['ap-ssid'] = new['ap-ssid']
    accepted['ap-pass'] = new['ap-pass']
    if (save_json('net.json', accepted)):
        return json.dumps({'net': accepted}), 202, {"Content-type": "application/json"}
    else:
        return json.dumps({'message': 'Cannot save', 'data': accepted}), 500, {"Content-type": "application/json"}

@server.route("/api/secure/pixelprograms", methods=["PUT", "PATCH"])
def change_pixelprograms(request):
    if ('user' in request.headers):
        user = request.headers['user']
        if ('token' in request.headers):
            accessToken = request.headers['token']
            users = load_json('users.json')
            if (user in users):
                if (accessToken == users[user]['token']):
                    old = load_json('pixelprograms.json')
                    pixelprograms = request.data
                    if (request.method == "PUT"):
                        if (save_json('pixelprograms.json', pixelprograms)):
                            new_credentials = refresh_token(user)
                            return json.dumps({'old': old, 'new': pixelprograms, 'newCredentials': new_credentials}), 200, {"Content-type": "application/json"}
                        else:
                            return json.dumps({'message': 'Cannot save', 'pixelprograms': pixelprograms}), 500, {"Content-type": "application/json"}
                    else:
                        new = old.copy()
                        new.extend(pixelprograms)
                        if (save_json('pixelprograms.json', new)):
                            new_credentials = refresh_token(user)
                            return json.dumps({'old': old, 'new': new_credentials}), 200, {"Content-type": "application/json"}
                        else:
                            return json.dumps({'message': 'Cannot save', 'pixelprograms': pixelprograms}), 500, {"Content-type": "application/json"}
    return json.dumps({}), 401, {"Content-type": "application/json"}

@server.route("/api/data", methods=["GET"])
def get_data(request):
    return json.dumps(load_json('data.json')), 200, {"Content-type": "application/json"}

@server.route("/api/current-state", methods=["GET"])
def get_current_state(request):
    return json.dumps(driver.current_state()), 200, {"Content-type": "application/json"}

@server.route("/api/pixelprograms", methods=["GET"])
def get_pixelprograms(request):
    return json.dumps(load_json('pixelprograms.json')), 200, {"Content-type": "application/json"}
    
@server.catchall()
def catchall(request):
    return json.dumps({"massage": "Page not exists"}), 404, {"Content-type": "application/json"}
