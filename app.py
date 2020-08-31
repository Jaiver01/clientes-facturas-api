from flask import Flask, request, jsonify, Response
from flask_pymongo import PyMongo
from flask_cors import CORS
from datetime import datetime
from bson import json_util, ObjectId
from sendEmail import sendEmail

app = Flask(__name__)
app.config['MONGO_URI'] = 'mongodb://prueba:pass77--@ds211829.mlab.com:11829/clientes-facturas'
CORS(app)

mongo = PyMongo(app)

@app.route('/clients', methods = ['GET'])
def getClients():
    clients = mongo.db.clients.find()
    response = json_util.dumps(clients)

    return Response(response, mimetype = 'application/json')

@app.route('/invoice', methods = ['POST'])
def createInvoice():
    try:
        invoice = {
            "code": request.json['code'],
            "client": ObjectId(request.json['client']),
            "total": request.json['total'],
            "withholdingTax": request.json['withholdingTax']
        }
    except:
        return {"done": False, "message": "Datos incorrectos para crear la factura"}

    if invoice['code'] and invoice['client'] and invoice['total']:
        invoice['id'] = mongo.db.invoices.insert({
            "code": invoice['code'],
            "client": invoice['client'],
            "total": float(invoice['total']),
            "withholdingTax": float(invoice['withholdingTax']),
            "date": datetime.now(),
            "state": "primerrecordatorio",
            "paid": False
        })
    else:
        return {"done": False, "message": "Datos incorrectos para crear la factura"}

    return {"done": True, "invoice": str(invoice['id'])}

@app.route('/invoices/<client>', methods = ['GET'])
def updateInvoices(client = None):
    return checkInvoices(client)

@app.route('/invoices', methods = ['GET'])
def updateInvoice():
    return checkInvoices()

def checkInvoices(client = None):
    cond = {}
    if client:
        try:
            cond = {"client": ObjectId(client)}
        except:
            return {"done": False, "message": "Datos incorrectos para obtener las facturas"}

    invoices = mongo.db.invoices.find(cond);
    invoices = json_util.dumps(invoices)

    states = {
        "segundorecordatorio": {},
        "desactivado": {}
    }
    for invoice in json_util.loads(invoices):
        state = None;
        if invoice['state'] == "primerrecordatorio":
            state = "segundorecordatorio"

            mongo.db.invoices.update_one({"_id": invoice['_id']}, {"$set": { "state": state }})
        elif invoice['state'] == "segundorecordatorio":
            state = "desactivado"            

        if state:
            try:
                states[state][str(invoice['client'])].append(invoice)
            except:
                states[state][str(invoice['client'])] = []
                states[state][str(invoice['client'])].append(invoice)

    for client in states['segundorecordatorio']:
        clientInfo = mongo.db.clients.find_one({"_id": ObjectId(client)})
        clientInfo = json_util.dumps(clientInfo)
        clientInfo = json_util.loads(clientInfo)
        clientInfo['invoices'] = states['segundorecordatorio'][client]

        sendEmail(clientInfo, 'Segundo Recordatorio')

    for client in states['desactivado']:
        if (len(states['desactivado'][client]) > 3):
            total = 0
            for invoice in states['desactivado'][client]:
                total += invoice['total']

            if total >= 10000:
                invs = [invoice['_id'] for invoice in states['desactivado'][client]]
                mongo.db.invoices.update_many({"_id": {"$in": invs}}, {"$set": { "state": "desactivado" }}, False)

                clientInfo = mongo.db.clients.find_one({"_id": ObjectId(client)})
                clientInfo = json_util.dumps(clientInfo)
                clientInfo = json_util.loads(clientInfo)
                clientInfo['invoices'] = states['desactivado'][client]

                sendEmail(clientInfo, 'Desactivado')

    invoices = mongo.db.invoices.find(cond)
    response = json_util.dumps(invoices)

    return Response(response, mimetype = 'application/json')

@app.errorhandler(404)
def notFound(error = None):
    response = jsonify({
        "done": False,
        "message": "Resource Not Found",
        "status": 404
    })

    response.status_code = 404
    return response

if __name__ == "__main__":
    app.run(debug = True)