from flask import Flask, render_template, request, redirect, render_template_string
from flask_mail import Mail, Message
from werkzeug.utils import secure_filename
from bson import ObjectId
from pymongo import MongoClient
import os

EXTENSIONES = ["png", "jpg", "jpeg"]
app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "./static/fondos"

# En mi caso he utilizado PaperCut para la gestión de emails
app.config["MAIL_SERVER"] = "localhost"
app.config["MAIL_PORT"] = 25
mail = Mail(app)

def archivo_permitido(nombre):
    return "." in nombre and nombre.rsplit(".", 1)[1] in EXTENSIONES

client = MongoClient("mongodb://localhost:27017/")
basedatos = client.fondos_flask
colecc = basedatos.fondos

titulo = "Galería de fotos con Flask"

@app.route("/", methods=["GET", "POST"])
def index():
    return render_template("index.html", titulo=titulo, fondos= colecc.find(), activo="todos")

@app.route("/aportar", methods=["GET", "POST"])
def aportar():
    if request.method == "POST":
        if "b_cancelar" in request.form:
            return redirect("/")
    else:
        return render_template("aportar.html", titulo=titulo)

@app.route("/insertar", methods=["GET", "POST"])
def subir_imagen():
    if request.method == "POST":
        f = request.files["archivo"]
        if f.filename == "":
            mensaje = "Hay que indicar un archivo de fondo"
        else:
            if archivo_permitido(f.filename):
                archivo = secure_filename(f.filename)
                f.save(os.path.join(app.config["UPLOAD_FOLDER"], archivo))
                mensaje = "Fondo cargado correctamente"
                titulo = request.form.get("titulo")
                descripcion = request.form.get("descripcion")
                lista_tags = []
                if "animales" in request.form:
                    lista_tags.append("animales")
                if "naturaleza" in request.form:
                    lista_tags.append("naturaleza")
                if "ciudad" in request.form:
                    lista_tags.append("ciudad")
                if "deporte" in request.form:
                    lista_tags.append("deporte")
                if "personas" in request.form:
                    lista_tags.append("personas")
                nuevo_fondo = {
                    "titulo": titulo,
                    "descripcion": descripcion,
                    "fondo": archivo,
                    "tags": lista_tags
                }
                colecc.insert(nuevo_fondo)
            else:
                mensaje = "¡El archivo indicado no es una imagen!"
    return render_template("aportar.html", mensaje=mensaje)

@app.route("/galeria", methods=["GET", "POST"])
def mostrar_galeria():
    tema = request.args.get("tema")
    fondos = []
    estilos = {"active": ""}
    if tema:
        fondos = colecc.find({"tags": {"$in": [tema]}})
        estilos["active"] = tema
    else:
        fondos = colecc.find()
    return render_template("index.html", titulo=titulo, fondos=fondos, activo=estilos["active"])

@app.route("/form_email", methods=["GET", "POST"])
def definir_email():
    id = request.args.get("_id")
    fondo = None
    if id:
        fondo = colecc.find_one({"_id": ObjectId(id)})
    return render_template("form_email.html", fondo = fondo["fondo"], id=id, titulo=fondo["titulo"], descripcion=fondo["descripcion"])

@app.route("/email", methods=["GET", "POST"])
def enviar_email():
    id_fondo = request.form.get("_id")
    fondo = colecc.find_one({"_id": ObjectId(id_fondo)})
    msg = Message("Fondos de pantalla Flask", sender="alumno@cepibase.int")
    msg.recipients = [request.values.get("email")]
    msg.html = render_template("email.html", titulo=fondo["titulo"], descripcion=fondo["descripcion"])
    with open(f"static/fondos/{fondo['fondo']}", "rb") as adj:
        tipo_archivo = "image/jpeg" if fondo["fondo"].lower().endswith(".jpg") else "image/png"
        msg.attach(fondo["fondo"], tipo_archivo, adj.read())
    mail.send(msg)
    return redirect("/")

if __name__ == "__main__":
    app.run()