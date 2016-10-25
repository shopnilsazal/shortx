from flask import Flask, request, jsonify, redirect, abort, render_template
from pymongo import MongoClient
from datetime import datetime
import random

client = MongoClient('mongodb://localhost:27017/')
db = client['shortx']

app = Flask(__name__)


def valid_url(long_url):
    protocol_exists = False
    protocols = ['http://', 'https://', 'ftp://', 'ftps://']
    if '.' not in long_url:
        return False
    if long_url.rfind('.') == len(long_url)-1:
        return False
    for protocol in protocols:
        if protocol in long_url:
            protocol_exists = True
    return protocol_exists


def already_exists(alias):
    urls = db.urls
    if urls.find_one({'short_url': alias}):
        return True
    return False


def shorten(alias):
    while already_exists(alias) or alias == '':
        alias = ''.join(random.choice('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqstuvwxyz') for i in range(6))
    return alias


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/<short_url>', methods=['GET'])
def redirect_short_url(short_url):
    urls = db.urls

    try:
        q = urls.find_one({'short_url': short_url})
        u = urls.update_one({'short_url': short_url}, {'$inc': {'clicks': 1}})
        long_url = q['long_url']
        return redirect(long_url)
    except:
        return abort(400)


@app.route('/api/url', methods=['GET'])
def list_all_url():
    urls = db.urls

    output = []
    status = 200

    for q in urls.find():
        output.append({
            'long_url': q['long_url'],
            'short_url': q['short_url'],
            'clicks': q['clicks'],
            'created_at': q['created_at']
        })
    return jsonify({'result': output}), status


@app.route('/api/url', methods=['POST'])
def add_url():
    urls = db.urls

    if request.json:
        long_url = request.json['long_url']
        short_url = request.json['short_url'] if request.json['short_url'] else shorten('')
    else:
        long_url = request.form['long-url']
        short_url = request.form['short-url'] if request.form['short-url'] else shorten('')

    url_id = urls.insert({
        'long_url': long_url,
        'short_url': short_url,
        'clicks': 0,
        'created_at': datetime.now()
    })

    new_url = urls.find_one({'_id': url_id})
    output = {
        'long_url': new_url['long_url'],
        'short_url': new_url['short_url'],
        'clicks': new_url['clicks'],
        'created_at': new_url['created_at']
    }
    status = 200

    if request.json:
        return jsonify({'result': output}), status
    return render_template('index.html', shorted_url=request.url_root+output['short_url'])


@app.route('/api/url/<short_url>', methods=['GET'])
def list_single_url(short_url):
    urls = db.urls

    q = urls.find_one({'short_url': short_url})
    output = {
        'long_url': q['long_url'],
        'short_url': q['short_url'],
        'clicks': q['clicks'],
        'created_at': q['created_at']
    }
    status = 200

    return jsonify({'result': output}), status


@app.route('/api/url/<short_url>', methods=['DELETE'])
def delete_url(short_url):
    urls = db.urls
    if urls.find_one({'short_url': short_url}):
        d = urls.delete_one({'short_url': short_url})
        output = {
            'result': short_url+' Successfully deleted.'
        }
        return jsonify(output), 200


if __name__ == '__main__':
    app.run(debug=True)

