import os
import json
import tornado.ioloop
import tornado.web
from pymongo import MongoClient

mongo_bdd = os.getenv('mongo_bdd')
mongo_bdd_server = os.getenv('mongo_bdd_server')
mongo_user = os.getenv('MONGO_INITDB_ROOT_USERNAME')
mongo_password = os.getenv('MONGO_INITDB_ROOT_PASSWORD')

database_uri = f'mongodb://{mongo_user}:{mongo_password}@{mongo_bdd_server}/'
client = MongoClient(database_uri)
db = client[mongo_bdd]

def get_next_id(collection_name):
    counter = db.counters.find_one_and_update(
        {"_id": collection_name},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=True
    )
    return counter["seq"]

class ImpresoraPorIPHandler(tornado.web.RequestHandler):
    def set_default_headers(self):
        self.set_header('Access-Control-Allow-Origin', '*')
        self.set_header('Access-Control-Allow-Headers', '*')
        self.set_header('Access-Control-Allow-Methods', '*')

    def options(self, ip):
        pass

    def get(self, ip):
        try:
            impresora = db.impresoras.find_one({"ip": ip})
            if impresora:
                impresora.pop('_id', None)
                self.write(json.dumps(impresora))
            else:
                self.set_status(404)
                self.write(json.dumps({"error": "Impresora no encontrada"}))
        except Exception as e:
            self.set_status(400)
            self.write(json.dumps({"error": str(e)}))
class ImpresorasHandler(tornado.web.RequestHandler):
    def set_default_headers(self):
        self.set_header('Access-Control-Allow-Origin', '*')
        self.set_header('Access-Control-Allow-Headers', '*')
        self.set_header('Access-Control-Allow-Methods', '*')

    def options(self):
        pass

    def get(self):
        impresoras = list(db.impresoras.find())
        for item in impresoras:
            item.pop('_id', None)
        self.write(json.dumps(impresoras))

    def post(self):
        try:
            data = json.loads(self.request.body)
            new_id = get_next_id("impresoras")
            db.impresoras.insert_one({
                "id": new_id,
                "ip": data["ip"],
                "nombre": data["nombre"]
            })
            self.write(json.dumps({"id": new_id}))
        except Exception as e:
            self.set_status(400)
            self.write(json.dumps({"error": str(e)}))

    def put(self):
        try:
            data = json.loads(self.request.body)
            update_data = {}
            if "ip" in data:
                update_data["ip"] = data["ip"]
            if "nombre" in data:
                update_data["nombre"] = data["nombre"]

            db.impresoras.update_one({"id": data["id"]}, {"$set": update_data})
            self.write(json.dumps({"status": "updated"}))
        except Exception as e:
            self.set_status(400)
            self.write(json.dumps({"error": str(e)}))

    def delete(self):
        try:
            data = json.loads(self.request.body)
            db.impresoras.delete_one({"id": data["id"]})
            self.write(json.dumps({"status": "deleted"}))
        except Exception as e:
            self.set_status(400)
            self.write(json.dumps({"error": str(e)}))

class PrintOrderHandler(tornado.web.RequestHandler):
    def set_default_headers(self):
        self.set_header('Access-Control-Allow-Origin', '*')
        self.set_header('Access-Control-Allow-Headers', '*')
        self.set_header('Access-Control-Allow-Methods', '*')

    def options(self, *args, **kwargs):
        pass

    def post(self):
        try:
            data = json.loads(self.request.body)
            new_id = get_next_id("ordenes_impresion")
            db.ordenes_impresion.insert_one({
                "id": new_id,
                "documento_html": data["documento_html"],
                "ip": data["ip"],
                "estado": False
            })
            self.write(json.dumps({"id": new_id}))
        except Exception as e:
            self.set_status(400)
            self.write(json.dumps({"error": str(e)}))

    def get(self, ip):
        try:
            ordenes = list(db.ordenes_impresion.find({"ip": ip}))
            for item in ordenes:
                item.pop('_id', None)
            self.write(json.dumps(ordenes))
        except Exception as e:
            self.set_status(400)
            self.write(json.dumps({"error": str(e)}))

    def patch(self, oid, estado):
        try:
            estado_bool = estado.lower() == 'true'
            db.ordenes_impresion.update_one({"id": int(oid)}, {"$set": {"estado": estado_bool}})
            self.write(json.dumps({"status": "estado actualizado"}))
        except Exception as e:
            self.set_status(400)
            self.write(json.dumps({"error": str(e)}))

def make_app():
    return tornado.web.Application([
        (r"/impresoras", ImpresorasHandler),
        (r"/impresoras/([^/]+)", ImpresoraPorIPHandler),
        (r"/print_order", PrintOrderHandler),
        (r"/print_order/([^/]+)", PrintOrderHandler),
        (r"/print_order/([^/]+)/([^/]+)", PrintOrderHandler),
    ])

if __name__ == "__main__":
    app = make_app()
    app.listen(5055)
    print("WebService disponible en http://localhost:5055")
    tornado.ioloop.IOLoop.current().start()
