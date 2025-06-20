from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

@app.route('/', methods=['GET'])
def base():
    return render_template("base.html")

if __name__ == '__main__':
    app.run(debug=True)