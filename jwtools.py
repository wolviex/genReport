import re
from datetime import date
from collections import Counter
import numpy


def mJoin(s1,s2,list):
	l = []
	for x in list:
		l.append(s2.join(x))
	return s1.join(l)

def stringScore(str1, str2):
	s1List = re.split(" |-",str1)
	s2List = re.split(" |-",str2)
	score = 0
	for x in range(len(s1List)):
		for y in range(len(s2List)):
			if s1List[x].lower() == s2List[y].lower():
				print "{} {}".format(s1List[x],s2List[y])
				score += 1
	return score

def strDistance(str1, str2):
	str1Len = len(str1)
	str2Len = len(str2)
	sTable = [[i] for i in range(str1Len+1)]
	del sTable[0][0]
	sTable[0] = [j for j in range(str2Len+1)]

	for i in range(1,str1Len+1):
		for j in range(1,str2Len+1):
			if str1[i-1] == str2[j-1]:
				sTable[i].insert(j,sTable[i-1][j-1])
			else:
				minimum = min(sTable[i-1][j]+1,sTable[i][j-1]+1,sTable[i-1][j-1]+1)
				sTable[i].insert(j,minimum)
	return sTable[-1][-1]

def wordDistance(str1, str2):
	word1List = str1.split(" ")
	word2list = str2.split(" ")
	w1Len = len(word1List)
	w2Len = len(word2list)

def filterArray(array, *filters):
	fil = [numpy.where(array[0]==f)[0][0] for f in filters]
	if len(filters) > 0:
		return array[:,fil]
	else:
		return array


#TODO
#Make a universal config system
def getConfig(name):
	f = file("ServerIdentity.txt","r")
	j = f.read()
	f.close()
	return j