#!/usr/bin/env python3

import redis
import json
import ast
from flask import Flask
from flask import jsonify
from flask import request

app = Flask(__name__)

r = redis.StrictRedis(host='localhost', port=6379, db=0)

r.sadd('ph', *set([7,2,0,4,3,8,1,4,4,2]))

def keyWord(word):
	return ''.join(sorted(word)).lower()

@app.route("/words.<format>", methods=['POST'])
def words(format=None):
	if request.method == 'POST':
		data_str = str(request.form.to_dict())
		data_str = data_str[2:-7]
		# to dict
		data_dict = json.loads(data_str)
		# to json
		data = jsonify(data_dict)
		# returns json object
		return data, 201

@app.route("/anagrams/<word>.<format>", methods=['GET'])
def word(word=None, format=None):
	if request.method == 'GET':
		anagrams = list(r.smembers(keyWord(word=word)))
		return jsonify({'anagrams' : anagrams}), 200




