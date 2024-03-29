#!/usr/bin/python
# -*- coding: utf-8 -*-


from gensim import corpora
from gensim import corpora, models, similarities
from gensim.models import hdpmodel, ldamodel
import operator
import util
import Constants
import os
import json
import math
from numpy import zeros
import numpy as np
from time import time
def printNormalRankedDocs(clarityScore, usedTestFiles):
    result = False
    try:
        testScore = clarityScore.sum(axis=1)
        testMapping = {}
        for files in range(len(usedTestFiles)):
            testMapping[usedTestFiles[files]] = testScore[files] 
        sorted_x = sorted(testMapping.items(), key=operator.itemgetter(1), reverse=True)
        todayDateFolder = util.getTodayDateFolder()
        write_directory = os.path.join(Constants.ROOT_FOLDER,Constants.RECOMMENDATION_DIR,Constants.ENGINE_DIR,
                                       todayDateFolder, Constants.GOOGLENEWS)
        if not os.path.exists(write_directory):
                os.makedirs(write_directory)
        outfile = open(os.path.join(write_directory,Constants.CLARITY_FILE), 'w')
        json_write = {}
        count = 1
        for (key,val) in sorted_x:
            json_write[key] = count
            count = count + 1
        json.dump(json_write, outfile)
        outfile.close()
        result = True
    except Exception, e:
        util.logger.error("Exception at printing Google Clarity docs for data : %s" % write_directory)
    return result

def printSuggRankedDocs(clarityScore, usedTestFiles):
    result = False
    try:
        testScore = clarityScore.sum(axis=1)
        testMapping = {}
        for files in range(len(usedTestFiles)):
            testMapping[usedTestFiles[files]] = testScore[files] 
        sorted_x = sorted(testMapping.items(), key=operator.itemgetter(1), reverse=True)
        todayDateFolder = util.getTodayDateFolder()
        write_directory = os.path.join(Constants.ROOT_FOLDER,Constants.RECOMMENDATION_DIR,Constants.ENGINE_DIR,
                                       todayDateFolder, Constants.SUGG_GOOGLENEWS)
        if not os.path.exists(write_directory):
                os.makedirs(write_directory)
        outfile = open(os.path.join(write_directory,Constants.CLARITY_FILE), 'w')
        json_write = {}
        count = 1
        for (key,val) in sorted_x:
            json_write[key] = count
            count = count + 1
        json.dump(json_write, outfile)
        outfile.close()
        result = True
    except Exception, e:
        util.logger.error("Exception at printing Sugg Clarity docs for data : %s" % write_directory)
    return result

def ConnectionClarity():
    todayDate = util.getYesterdayDateFolder()
    lastClarityDate = util.loadSettings(Constants.LAST_CLARITY_DIR)
    lastSuggClarityDate = util.loadSettings(Constants.LAST_SUGG_CLARITY_DIR)
    if lastClarityDate:
        util.logger.info("Google Clarity done last for ="+lastClarityDate)
    else:
        util.logger.info("Google Clarity done last for none")
    if lastSuggClarityDate:
        util.logger.info("Sugg Clarity done last for ="+lastClarityDate)
    else:
        util.logger.info("Sugg Clarity done last for none")
        
    if todayDate == lastClarityDate and todayDate == lastSuggClarityDate:
        util.logger.info("Clarity signal done for today =" + todayDate)
        return True
    
    trainFiles = util.findTrainingFiles()
    trainFiles = util.random_select(trainFiles)
    trainCorpus, usedTrainFiles = util.findCorpus(trainFiles)
    
    normalClarity = True
    if todayDate != lastClarityDate:
        testFiles = util.findTestFiles()
        testCorpus, usedTestFiles = util.findCorpus(testFiles)   
        clarityobj = Clarity(trainCorpus,testCorpus)
        clarityScore = clarityobj.ClarityScore()
        normalClarity = printNormalRankedDocs(clarityScore, usedTestFiles)
        if normalClarity == True:
            util.saveSettings(Constants.LAST_CLARITY_DIR, todayDate)
            util.logger.info("Google Clarity info just completed for ="+todayDate)
            
    suggClarity = True
    if todayDate != lastClarityDate:
        testFiles = util.findSuggTestFiles()
        testCorpus, usedTestFiles = util.findCorpus(testFiles)   
        clarityobj = Clarity(trainCorpus,testCorpus)
        clarityScore = clarityobj.ClarityScore()
        suggClarity = printSuggRankedDocs(clarityScore, usedTestFiles)
        if suggClarity == True:
            util.saveSettings(Constants.LAST_SUGG_CLARITY_DIR, todayDate)
            util.logger.info("SuggGoogle Clarity info just completed for ="+todayDate)
            
    return normalClarity or suggClarity

class Clarity:
    
    def __init__(self, fn_docs, test_docs) :
        self.NUM_RELEVANT = 5
        self.fn_docs = fn_docs
        self.test_docs = test_docs
        self.N = 0
        self.DocAvgLen = 0
        self.wGivenR = []
        self.DF = {}
        self.DocTF = []
        self.DocLen = []
        self.DocIDF = {}
        self.buildDictionary()
        self.TFIDF_Generator()
        self.init_tfidf()
        
    def buildDictionary(self) :
        docs = self.fn_docs
        all_tokens = sum(docs, [])
        tokens_once = set(word for word in set(all_tokens) if all_tokens.count(word) == 1)
        TotWords = len(all_tokens) - len(tokens_once)
        self.trainCorpus = [[word for word in text if word not in tokens_once]
         for text in docs]
        self.trainCorpus = [x for x in self.trainCorpus if x != []]
        self.N = len(self.trainCorpus)
        self.dictionary = corpora.Dictionary(self.trainCorpus)
        try:
            self.DocAvgLen = TotWords/self.N
        except Exception, e:
            self.DocAvgLen = 0
            util.logger.error("Divide by zero error in clarity")
        if self.N < self.NUM_RELEVANT:
            self.NUM_RELEVANT = self.N
        self.TotWords = TotWords
        
    def TFIDF_Generator(self, base=math.e) :
        trainCorpus = self.trainCorpus
        for doc in trainCorpus:
            self.DocLen.append(len(doc))
            bow = dict([(term, freq*1.0/len(doc)) for term, freq in self.dictionary.doc2bow(doc)])
            for term, tf in bow.items() :
                if term not in self.DF :
                    self.DF[term] = 0
                self.DF[term] += 1
            self.DocTF.append(bow)
        try:
            wGivenC = [float(self.DF[term])/self.TotWords for term in range(len(self.dictionary.keys()))]    
            self.wGivenC = np.asarray(wGivenC)
        except Exception, e:
            self.wGivenC = 0
            util.logger.error("Divide by zero error in clarity")
        
        
    def init_tfidf(self):
         corpus = [self.dictionary.doc2bow(text) for text in self.trainCorpus]
         self.tfidf = models.TfidfModel(corpus=corpus, id2word=self.dictionary,normalize=True)
         self.index = similarities.SparseMatrixSimilarity(self.tfidf[corpus],num_features=len(self.dictionary))
         
    def findMostRelevant(self,vec):
         sims = self.index[self.tfidf[vec]]
         sorted_index = [i[0] for i in sorted(enumerate(sims), key=lambda x:x[1], reverse = True)]
         return sorted_index[:self.NUM_RELEVANT]
    
    def computeWgivenRdash(self,trainIdx, testQuery, listRelevant):
        wGivenRdash = np.ones(self.NUM_RELEVANT)
        
        trainQuery = self.trainCorpus[trainIdx]
        testDoc = dict(testQuery)
        trainDoc = dict(self.dictionary.doc2bow(trainQuery))
        commonTerms = set(testDoc.keys()) & set(trainDoc.keys())
        
        
        for term in commonTerms :
            trainWordLen = trainDoc[term]
            testWordLen = testDoc[term]
            power = trainWordLen if trainWordLen < testWordLen else testWordLen
            wGivenRdash = wGivenRdash * np.asarray([math.pow(doc[term], power) if term in doc else 1    for doc in listRelevant])
        return wGivenRdash
                
                
                    
    def ClarityScore(self) :     
        finalScore=zeros((len(self.test_docs),self.N))
        for tstIndex, testText in enumerate(self.test_docs):
            testQuery = self.dictionary.doc2bow(testText)
            relevantSet = self.findMostRelevant(testQuery)
            listRelevant = []
            tokens = self.dictionary.keys()
            for i in range(self.NUM_RELEVANT):
                relevantQuery = self.DocTF[relevantSet[i]]
                listRelevant.append(relevantQuery)
            for idx, trainDoc in enumerate(self.DocTF):
                try:
                    t0 = time()
                    wGivenRdash = self.computeWgivenRdash(idx, testQuery, listRelevant)
                    wGivenR = [ [ doc[term] if term in doc else 0 for term in range(len(self.dictionary.keys()))]  for doc in listRelevant]
                    wGivenR = np.asarray(wGivenR)
                    wGivenSD = [wGivenR[x]*wGivenRdash[x] for x in range(self.NUM_RELEVANT) ]
                    wGivenSD = np.asarray(wGivenSD)
                    finalWSD = wGivenSD[0] + wGivenSD[1] + wGivenSD[2] + wGivenSD[3] + wGivenSD[4] 
                    temp1 = finalWSD/self.wGivenC
                    temp2 = np.where(temp1>0, np.log(temp1), 0)
                    #temp2 = np.log(temp1)
                    prod = temp2 * finalWSD
                    finalScore[tstIndex][idx] = np.sum(prod)
                    t1 = time()
                    #print "for %d and %d it took %d seconds score = %f" % (tstIndex, idx, t1-t0, finalScore[tstIndex][idx])
                    pass
                except Exception, e:
                    finalScore[tstIndex][idx] = 0
                    util.logger.error("Divide by zero error in clarity")
        return finalScore
                
    def BM25Score(self, Query=[], k1=1.5, b=0.75) :
        query_bow = self.dictionary.doc2bow(Query)
        scores = []
        for idx, doc in enumerate(self.DocTF) :
            #t0 = time()
            query_terms = dict(query_bow).keys()
            doc_terms = doc.keys()
            #t1 = time()
            #print "time 5 = "+str(t1-t0)
            if len(query_terms) < len(doc_terms):
                commonTerms = [word for word in query_terms if word  in doc_terms]
            else:
                commonTerms = [word for word in doc_terms if word  in query_terms]
           # t2 = time()
          #  print "time 6 = "+str(t2-t1)
           # commonTerms = set(dict(query_bow).keys()) & set(doc.keys())
            tmp_score = []
            doc_terms_len = self.DocLen[idx]
            for term in commonTerms :
                upper = (doc[term] * (k1+1))
                below = ((doc[term]) + k1*(1 - b + b*doc_terms_len/self.DocAvgLen))
                tmp_score.append(self.DocIDF[term] * upper / below)
            #t3 = time()
            #print "time 7 = "+str(t3-t2)
            scores.append(sum(tmp_score))
        return np.array(scores)

            