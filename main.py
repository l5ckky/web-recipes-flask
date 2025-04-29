from flask import Flask, render_template, request, jsonify
import requests
import json
from bs4 import BeautifulSoup
from time import sleep
import api

app = Flask(__name__)


# base = 'https://www.russianfood.com'


@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html')


@app.route('/search', methods=['POST'])
def search():
    if request.method == 'POST':
        ingredients = list(filter(lambda x: x[0], request.values.listvalues()))[0]
        print(ingredients)
        # if not ingredients:
        #     return jsonify({'recipes': []})

        response = api.scrape_recipes(ingredients)
        return render_template('index.html',
                               recipes=response['recipes'],
                               msg=response['msg'])
    elif request.method == 'GET':
        return "error"


# return render_template('index.html', recipes=recipes)


if __name__ == '__main__':
    app.run(port=8080, host='127.0.0.1', debug=True)
