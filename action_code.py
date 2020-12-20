# -- coding: utf-8 --

from flask import Flask, jsonify, request, make_response, Response
from flask_restful import Api, Resource
import json
import time
import clustering
import time
import pickle
import random
from clustering_copy import Cluster
import threading

# # time.sleep(0.5)

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False
api = Api(app)
global_topics = []
global_topics_english=[]
global_year_gap = 5
global_topic_2010_2020 = pickle.load(open('./2010_2020_topics.pickle', 'rb'))

clus = Cluster()

abstract = ''

def recommend_topic(period):
    global global_topic_2010_2020
    global global_topics_english
    global_topics_english = random.sample(global_topic_2010_2020, 3)
    return clus.papago(', '.join(global_topics_english), None)

def recommend_paper(topics_text):
    global clus
    return clus.recommend_paper(topics_text)

def read_Abstract():
    print()

class GetParams_paper(Resource):
    def post(self):
        data = request.get_json()
        # print(data)
        topics = ', '.join(data['action']['parameters']['topic']['value'].split('|'))
        return_topics = ', '.join(topics)

        papers = recommend_paper(' '.join(clus.papago(topics, None).split(', ')))

        return {
            "version": "2.0",
            "resultCode": "OK",
            "output": {
            "return_topic": return_topics,
            "paper_name_english": papers[0],
            "paper_name_korean": '',
            "paper_author": '',
            "paper_publish": '',
            "paper_year": ''
            }
                }

class GetParams_read_Abstract(Resource):
    def post(self):
        global global_topics
        data = request.get_json()
        # print(data)

        return {
            "version": "2.0",
            "resultCode": "OK",
            "output": {
                "paper_abstract": '요약문임 대충이거ㅋ'
                }
        }

############################################################################

class GetParams_topic(Resource):
    def post(self):
        data = request.get_json()
        # print(data)
        year = 5  #디폴트는 최근 5년

        if 'year' in data['action']['parameters']:  # 사용자가 지정한 연도가 있다면
            year = data['action']['parameters']['year']['value']

        year_column = str(2020 - int(year) + 1) + '-' + str(2020)
        global global_topics
        global_topics = recommend_topic(year).split(', ')

        t = threading.Thread(target=clus.recommend_paper, args=[' '.join(global_topics_english)])
        t.start()

        #파일 열고 year 에 해당하는 주제 반환
        #주제는 번역해서 반환
        return {
            "version": "2.0",
            "resultCode": "OK",
            "output": {
            "period": year_column
            ,
            "topic1": global_topics[0],
            "topic2": global_topics[1],
            "topic3": global_topics[2]}
                }

class GetParams_topic2paper(Resource):
    def post(self):
        global global_topics
        data = request.get_json()
        # print("============================")
        # print(clus.paper_name)
        # print(clus.paper_year)
        # print(clus.paper_abstract)
        # print("============================")
        # print(papago(clus.paper_name))

        return {
            "version": "2.0",
            "resultCode": "OK",
            "output": {
                "paper_name_english_": clus.paper_name,
                "paper_name_korean_": clus.papago(clus.paper_name, None),
                "paper_publish_": 'NIPS',
                "paper_year_": str(clus.paper_year)}
                }

class GetParams_readAbstract(Resource):
    def post(self):
        global global_topics
        data = request.get_json()
        # print(data)

        text = {
            "version": "2.0",
            "resultCode": "OK",
            "output": {
                "paper_abstract_": clus.paper_abstract
                }
            }

        return Response(json.dumps(text, ensure_ascii=False).encode('utf8'), content_type='application/json; charset=utf-8')

api.add_resource(GetParams_paper, '/answer.paper')
api.add_resource(GetParams_read_Abstract, '/branch_read_Abstract')

api.add_resource(GetParams_topic, '/answer.topic')
api.add_resource(GetParams_topic2paper, '/branch_topic2paper')
api.add_resource(GetParams_readAbstract, '/branch_readAbstract')
##
if __name__ == '__main__':
    app.run(debug=True)
    clus.driver.close()
