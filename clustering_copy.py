from sklearn.feature_extraction.text import TfidfVectorizer
from nltk.stem import WordNetLemmatizer
import nltk
import string
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity
import seaborn as sns
import numpy as np
import matplotlib.pyplot as plt
import copy
from selenium import webdriver
import time
class Cluster:
    def __init__(self):
        self.driver = webdriver.Chrome('./chromedriver')
        self.driver.get('https://papago.naver.com/')
        self.paper_name = ''
        self.paper_year = 0
        self.paper_abstract = ''

        self.remove_punct_dict = dict((ord(punct), None) for punct in string.punctuation)
        self.lemmar = WordNetLemmatizer()
        self.papers = pd.read_csv('./temp.csv')
        self.papers_copy =copy.deepcopy(self.papers)
        self.papers = self.papers.drop(['event_type', 'id', 'pdf_name', 'abstract'], axis=1)

        self.tfidf_vect, self.ftr_vect, self.kmeans = None,None,None
        self.cluster_centers, self.paper_idx0, self.paper_idx1, self.paper_idx2 =None,None,None,None

    def LemTokens(self, tokens):
        return [self.lemmar.lemmatize(token) for token in tokens]

    def LemNormalize(self, text):
        return self.LemTokens(nltk.word_tokenize(text.lower().translate(self.remove_punct_dict)))

    def cluster(self, papers):
        tfidf_vect = TfidfVectorizer(tokenizer=self.LemNormalize, stop_words='english', ngram_range=(1, 2), min_df=0.05, max_df=0.85)
        ftr_vect = tfidf_vect.fit_transform(papers['paper_text'])
        # print(papers['paper_text'])
        kmeans = KMeans(n_clusters=5, max_iter=10000, random_state=42)
        return tfidf_vect, ftr_vect, kmeans

    def training(self):
        cluster_label = self.kmeans.fit_predict(self.ftr_vect)
        # print(self.ftr_vect)
        self.papers['cluster_label'] = cluster_label

        cluster_centers = self.kmeans.cluster_centers_

        paper_idx0 = self.papers[self.papers['cluster_label'] == 0].index
        paper_idx1 = self.papers[self.papers['cluster_label'] == 1].index
        paper_idx2 = self.papers[self.papers['cluster_label'] == 2].index

        return cluster_centers, paper_idx0, paper_idx1, paper_idx2

    def recommend_paper(self, topics):
        print('클러스터링 시작')
        similarity = 0
        # print(topics)
        self.papers = self.papers.append({'year': '2020', 'title': 'test', 'paper_text': topics}, ignore_index=True)
        self.tfidf_vect, self.ftr_vect, self.kmeans = self.cluster(self.papers)

        self.cluster_centers, self.paper_idx0, self.paper_idx1, self.paper_idx2 = self.training()
        comparison_doc0 = self.papers.iloc[self.paper_idx0[len(self.paper_idx0)-1]]['title']
        comparison_doc1 = self.papers.iloc[self.paper_idx1[len(self.paper_idx1)-1]]['title']
        comparison_doc2 = self.papers.iloc[self.paper_idx2[len(self.paper_idx2)-1]]['title']

        if comparison_doc0 == self.paper_name:
            similarity = cosine_similarity(self.ftr_vect[self.paper_idx0[len(self.paper_idx0) - 1]], self.ftr_vect[self.paper_idx0])
            paper_idx = self.paper_idx0
        elif comparison_doc1 == self.paper_name:
            similarity = cosine_similarity(self.ftr_vect[self.paper_idx1[len(self.paper_idx1) - 1]], self.ftr_vect[self.paper_idx1])
            paper_idx = self.paper_idx1
        else:
            similarity = cosine_similarity(self.ftr_vect[self.paper_idx2[len(self.paper_idx2) - 1]], self.ftr_vect[self.paper_idx2])
            paper_idx = self.paper_idx2

        sorted_idx = similarity.argsort()[:,::-1]
        sorted_idx= sorted_idx[:,1:]

        paper_sorted_idx= paper_idx[sorted_idx.reshape(-1,)]
        paper_sim_values = np.sort(similarity.reshape(-1,))[::-1]
        paper_sim_values = paper_sim_values[1:]
        paper_sim_df = pd.DataFrame()

        paper_sim_df['title'] = self.papers.iloc[paper_sorted_idx]['title']
        paper_sim_df['similarity'] = paper_sim_values
        # print('-----------------------------------------')
        self.paper_name = ', '.join(paper_sim_df['title'][0:1])
        # self.paper_name = ''.join(paper_sim_df['title'][0])
        for i in range(len(self.papers_copy)):
            if self.papers_copy['title'][i] == self.paper_name:
                self.paper_year = self.papers_copy['year'][i]
                self.paper_abstract = self.papers_copy['paper_text'][i]
        self.paper_abstract = self.papago(self.paper_abstract, 1)
        print(self.paper_abstract)
        print('클러스터링 종료')

    def papago(self, text, t1):
        try:
            self.driver.find_element_by_css_selector('#sourceEditArea > button').click()
        except:
            pass
        self.driver.find_element_by_css_selector('#txtSource').send_keys(text)
        self.driver.find_element_by_css_selector('button#btnTranslate').click()
        if t1 == 1:
            time.sleep(5)
        time.sleep(0.5)
        result = self.driver.find_element_by_css_selector("div#txtTarget").text
        return result
# if __name__ == "__main__":
    # a = Cluster()
    # a.recommend_paper('artificial math model')
