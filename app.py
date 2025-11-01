from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv
import requests
import logging

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

#Compteur bits
data_cache = {
    "get":[],
    "get_bits":[],
    "patch":[],
    "patch_bits":[],
    "put":[],
    "put_bits":[]
}
def filtrer(liste):
    maintenant = time.time()
    liste_return = liste
    if len(liste_return) > 0:
        while liste_return and maintenant - liste_return[0] > 30:
            liste_return.pop(0)
        while len(liste_return) > len(data_cache[liste_return + "_bits"]):
            data_cache[liste_return + "_bits"].pop(0)
        
    return liste_return
def nettoyer_historique():
    """Supprime les entrées de plus de 30 secondes"""
    data_cache[get] = filtrer(data_cache[get])
    data_cache[patch] = filtrer(data_cache[patch])
    data_cache[put] = filtrer(data_cache[put])
    
@app.before_request
def enregistrer_requete():
    """Ajoute un horodatage à chaque requête"""
    nettoyer_historique()
    def bits_fonction(list):
        x = 0
        for item in list:
            x += item
        return x
    bits_json = {
        "get":bits_fonction(get_bits),
        "patch":bits_fonction(patch_bits),
        "put":bits_fonction(put_bits)
    }
    
    
@app.route('/', defaults={'subpath': ''}, methods=['GET','PUT','DELETE','PATCH'])
@app.route('/<path:subpath>', methods=['GET','PUT','DELETE','PATCH'])
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

    if ok == True and not subpath == "stats":
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
    elif ok == True and subpath == "stats":
        return jsonify(bits_json)
    else:
        return jsonify({"Message":"Acces refusé"})


@app.route("/wake", methods=["POST"])
def wake():
    data = request.get_json(force=True, silent=True) or {}
    cle_received = data.get('cle')
    if cle_received:
        resp = requests.post(f"{URL}cle-ultra", json={"cle": cle_received}, timeout=5 )
        resp.raise_for_status()
        j = resp.json()
        access = j.get("access")
        if not access == "false":
            return jsonify({"status": "ok"})
    return jsonify({"status": "error", "message": "clé invalide"})


if __name__ == '__main__':
    port = int(port)
    print(f"⚡️ Proxy firebase actif sur le port {port}")
    app.run(host='0.0.0.0', port=port)
