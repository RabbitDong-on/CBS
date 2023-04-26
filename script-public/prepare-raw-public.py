#!/usr/bin/python

import os,sys,re
import operator
from copy import deepcopy

SYSTEMS = ["cassandra", "hbase", "hdfs", "flume", "mapreduce", 'zookeeper']
tagcode = ["kb-","ll-","dc-","sc-","dr-", "mc-"]
valid_tags = []
raw_path = "../../raw"
jiraAPI_path = "../../script/jira-api/output"
output_path = "../raw-public"
issues ={}

def validtags():
	raw_tags = open('valid-tags.txt')
	for line in raw_tags:
		line = line.split('\n', 1)[0]
		if not line[:1] == "#" and not len(line.strip()) == 0:
			valid_tags.append(line)

def read(system):

	"""read raw data"""
	taglist = tuple(valid_tags)
	raw_file = open(raw_path+'/'+system+'.txt')
	key =""
	issues[system]={}
	for line in raw_file:
		line = line.strip()
		if line.find('[') == 0:
			key = line
			issues[system][key] =[]
		if (not line.startswith(' ') and line.startswith(taglist)):
			issues[system][key].append(prefix_match(line, taglist))

	""""copy the issues dict to small dict, to accomodate remove dict looping"""
	temp=deepcopy(issues[system])

	"""check the dictionary: if dict consist of empty tag or t-low tag, so remove the issue"""
	for key in temp:
		if not issues[system][key] or any('t-low' in tag for tag in issues[system][key]):
			issues[system].pop(key, None)

	"""read raw jira-api"""
	jiraAPI_file = open(jiraAPI_path+'/'+system+'.out')
	for line in jiraAPI_file:
		line = line.strip()
		if line.find('[') == 0:
			key = line
		if (not line.startswith(' ') and line.startswith(taglist)):
			if key in issues[system]:
				issues[system][key].append(line)

def prefix_match(line, taglist):
	for element in taglist:
		if line.startswith(element):
			return element

def write(system):
	output = open(output_path+'/'+system+'.txt', 'w')
	for key in natural_sort(issues[system]):
		output.write('\n'+ key +'\n')	#
		#print the content
		for tag in issues[system][key]:
			output.write(tag+ '\n')
	output.write('\n')

def natural_sort(l): 
    convert = lambda text: int(text) if text.isdigit() else text.lower() 
    alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', key) ] 
    return sorted(l, key = alphanum_key)

def main():
	"""1. Read valid tags"""
	print "parse valid-tags.txt...."
	validtags()
	for system in SYSTEMS:
		print "Preparing "+system+"...."
		"""2. parse system and filter"""
		read(system)
		"""3. create file"""
		write(system)
	print "Done."
if __name__ == '__main__':
	main()