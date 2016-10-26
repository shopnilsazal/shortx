from flask import Flask, request, jsonify, redirect, abort, render_template, flash, url_for
from pymongo import MongoClient
from datetime import datetime
import random

client = MongoClient('mongodb://localhost:27017/')
db = client['shortx']

app = Flask(__name__)
app.secret_key = 'cd48e1c22de0961d5d1bfb14f8a66e006cfb1cfbf3f0c0f3'


def valid_url(long_url):
    """
    Return True if param is a valid URL.
    :param long_url:
    :return: Boolean
    """
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
    """
    Check if alias already exists in database or not
    :param alias:
    :return: Boolean
    """
    urls = db.urls
    if urls.find_one({'short_url': alias}):
        return True
    return False


def shorten(alias):
    """
    Return shortened URl.
    :param alias:
    :return: String
    """
    while already_exists(alias) or alias == '':
        alias = ''.join(random.choice('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqstuvwxyz') for i in range(6))
    return alias


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/success')
def success():
    return render_template('success.html')


@app.route('/error')
def error():
    return render_template('404.html')


@app.route('/<short_url>', methods=['GET'])
def redirect_short_url(short_url):
    urls = db.urls

    try:
        q = urls.find_one({'short_url': short_url})
        u = urls.update_one({'short_url': short_url}, {'$inc': {'clicks': 1}})
        long_url = q['long_url']
        return redirect(long_url)
    except:
        flash('URL not found.')
        return redirect(url_for('error'))


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
        if valid_url(request.json['long_url']):
            long_url = request.json['long_url']
        else:
            return jsonify({'result': 'Please provide a valid URL.'})
        short_url = request.json['short_url'] if request.json['short_url'] else shorten('')
    elif request.form:
        if valid_url(request.form['long-url']):
            long_url = request.form['long-url']
        else:
            flash('Please provide a valid URL.')
            return redirect(url_for('error'))
        short_url = request.form['short-url'] if request.form['short-url'] else shorten('')
    else:
        return abort(400)

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
    flash('Your Shortened URL: '+request.url_root+output['short_url'])
    return redirect(url_for('success'))


@app.route('/api/url/<short_url>', methods=['GET'])
def list_single_url(short_url):
    urls = db.urls

    try:
        q = urls.find_one({'short_url': short_url})
        output = {
            'long_url': q['long_url'],
            'short_url': q['short_url'],
            'clicks': q['clicks'],
            'created_at': q['created_at']
        }
        status = 200
    except:
        return jsonify({'result': 'URL not found.'})

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
    else:
        jsonify({'result': 'URL not found.'})


if __name__ == '__main__':
    app.run(debug=True)

