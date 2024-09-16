#!/usr/bin/python
import flask
import book_signature_generator
import webbrowser
import threading
import werkzeug.utils
import os
import time
import signal

flaskapp = flask.Flask(__name__)
ip = "127.0.0.1"
port = 8283

@flaskapp.route("/")
def index():
     index_html = open("index.html", "r").readlines()
     return("".join(index_html))

def open_browser():
     webbrowser.open(f"http://{ip}:{port}")

@flaskapp.route("/process/", methods=["GET", "POST"])
def process_file():
     if flask.request.method == "POST":
         inner_margin = float(flask.request.form['inner_margin'])
         print(flask.request.form['binder_folio'])
         binder_folio = bool(flask.request.form['binder_folio'])
         page_margin = float(flask.request.form['page_margin'])
     elif flask.request.method == "GET":
         inner_margin = float(flask.request.args.get("inner_margin"))
         binder_folio = bool(flask.request.args.get('binder_folio'))
         page_margin = float(flask.request.args.get('page_margin'))
     infile = flask.request.files['infilename']
     if not infile:
         exit(1)
     infilename = werkzeug.utils.secure_filename(infile.filename)
     tmpfilename = f"tmpfiles/{infilename}"
     infile.save(tmpfilename)
     newfilename = f"{tmpfilename[:-4]}-book.pdf"
     book_signature_generator.convert_pdf(tmpfilename, newfilename, page_number_margin=page_margin, inner_margin=inner_margin, binder_folio=binder_folio)
     pdfdata = open(newfilename, "rb").read()
     response = flask.make_response(pdfdata)
     response.headers['Content-Type'] = 'application/pdf'
     response.headers['Content-Disposition'] = 'inline; filename="Spells.pdf"'
     return(response)

@flaskapp.route("/shutdown")
def shutdown_server():
     os.kill(os.getpid(), signal.SIGINT)
     return("program stopped")
     shutdown_function = flask.request.environ.get("werkzeug.server.shutdown")
     if shutdown_function is None:
         print("not running flask????")
         exit(-1)
     else:
         print("really shutting down")
         shutdown_function()

if __name__ == "__main__":
    if os.environ.get("WERKZEUG_RUN_MAIN") != "true":
        threading.Timer(1, open_browser).start()
    flaskapp.run(host=ip, port=port, debug=True)
