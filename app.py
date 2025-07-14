from flask import Flask, request, jsonify, send_from_directory
import pandas as pd
import os
from datetime import datetime

app = Flask(__name__)
@app.route('/')
def hello():
    return '안녕'

if __name__ == '__main__':
    app.run(port=5000)
