#!/usr/bin/python
import flask
import book_signature_generator
import webbrowser

flask = flask.Flask(__name__)

@app.route("/")
def index():
     index_html = open("index.html", "r").readlines()
     return(index.html)

if __name__ == "__main__":
    ip = "127.0.0.1"
    port = 81254
    flask.run(host=ip, port=port, debug=True)
    webbrowser.open(f"https://{ip}:{port}")
