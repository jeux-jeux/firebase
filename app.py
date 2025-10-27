from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv
import requests

app = Flask(__name__)
app.logger.setLevel(logging.DEBUG)

CLE = os.environ.get('CLE')
URL = os.environ.get('URL')

resp = requests.post(URL, json={"cle": CLE}, timeout=5 )
resp.raise_for_status()
j = resp.json()
firebase_url = j.get("firebase_url")
allowed = j.get("origine_stockage")
level = j.get("level")
port = j.get("port")

@app.route('/mail', defaults={'subpath': ''}, methods=['GET','PUT','DELETE','PATCH'])
@app.route('/mail/<path:subpath>', methods=['GET','PUT','DELETE','PATCH'])
def route(subpath):
    # Récupérer la méthode et le chemin complet
    if level == "nothing":
        ok = False
    elif level == "origin":
        origin = request.headers.get('Origin')
        if origin in allowed:
            ok = True
        else:
            ok = False
    else:
        ok = True
        
    data = request.get_json()
    cle_received = data.get('cle')
    if cle_received and ok == False:
        resp = requests.post(f"{URL}cle-ultra", json={"cle": cle_received}, timeout=5 )
        resp.raise_for_status()
        j = resp.json()
        access = j.get("access")
        if not access == "false":
            ok = True

    if cle_received and ok == False:
        resp = requests.post(f"{URL}cle-iphone", json={"cle": cle_received}, timeout=5 )
        resp.raise_for_status()
        j = resp.json()
        access = j.get("access")
        if not access == "false":
            ok = True

    if ok == True:
        method = request.method
        data.pop("cle", None)
        if method == 'GET':
            resp = requests.get(f"{firebase_url}{subpath}", json=data, timeout=5 )
            resp.raise_for_status()
            j = resp.json()
            return jsonify(j)
        elif method == 'PUT':
            resp = requests.put(f"{firebase_url}{subpath}", json=data, timeout=5 )
            resp.raise_for_status()
            j = resp.json()
            return jsonify(j)
        elif method == 'DELETE':
            resp = requests.delete(f"{firebase_url}{subpath}", json=data, timeout=5 )
            resp.raise_for_status()
            j = resp.json()
            return jsonify(j)
        elif method == 'PATCH':
            resp = requests.patch(f"{firebase_url}{subpath}", json=data, timeout=5 )
            resp.raise_for_status()
            j = resp.json()
            return jsonify(j)
        else:
            return jsonify({ 'error': "Méthode non ajoutée par le développeur."})


if __name__ == '__main__':
    port = int(port)
    print(f"⚡️ Proxy firebase actif sur le port {port}")
    app.run(host='0.0.0.0', port=port)
