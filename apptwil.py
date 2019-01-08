#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import io
import pymysql
from flask import Flask, request, Response, make_response, jsonify, url_for, redirect, session, render_template
import sys
import requests
import json
import urllib
# Twilio Helper Library
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Record, Gather, Say, Dial, Play
# Google Cloud SDK
from google.oauth2 import service_account
from google.cloud import speech
from google.cloud.speech import enums
from google.cloud.speech import types

#Initiate Flask app
app = Flask(__name__,template_folder='template')

#Set key for session variables
SECRET_KEY = os.environ["SECRET_KEY"]
app.secret_key=SECRET_KEY

# Declare global variables
cli = os.environ["cli"]
#dnis = os.environ["dnis"]
account_sid = os.environ["account_sid"]
auth_token = os.environ["auth_token"]
databasename = os.environ["databasename"]
databasehost = os.environ["databasehost"]
databaseusername = os.environ["databaseusername"]
databasepassword = os.environ["databasepassword"]
credentials_dgf = os.environ["GOOGLE_APPLICATION_CREDENTIALS"]

# Render Homepage to upload test cases
@app.route('/TestCaseUpload')
def load_TestCaseUploadPage():
	return render_template("FileUpload.html")

# Receive post request from HTML and call helper functions
@app.route('/UploadTestCaseToDB',methods = ['POST'])
def submitFileToDB():
	if request.method == 'POST':
		f = request.files['fileToUpload']
		f.save(f.filename)
		uploadTestCaseToDB(f.filename)
		createJSONStringForTestCases()
	return readTestCasesFromDB()

# Upload test case information to Database
def uploadTestCaseToDB(uploadedFileName):
	with open(uploadedFileName, "r") as ins:
		print(databasehost, databaseusername, databasepassword, databasename)
		conn = pymysql.connect(host=databasehost, user=databaseusername, passwd=databasepassword, port=3306, db=databasename)
		cur = conn.cursor()
		i=0
		for line in ins:
			print("line==>"+line)
			splittedTestCaseLine = line.split(",")
			caseID =splittedTestCaseLine[0]
			caseStepID = splittedTestCaseLine[1]
			action=splittedTestCaseLine[2]
			inputType = splittedTestCaseLine[3]
			inputValue = splittedTestCaseLine[4]
			inputpause = splittedTestCaseLine[5]
			expectedValue = splittedTestCaseLine[6]
			promptDuration = splittedTestCaseLine[7]
			query = "INSERT INTO ivr_test_case_master(testcaseid,testcasestepid,action,input_type,input_value,pause_break,expected_value,expected_prompt_duration) values (%s,%s,%s,%s,%s,%s,%s,%s)"	
			args = (caseID,caseStepID,action,inputType,inputValue,inputpause,expectedValue,promptDuration)
			if i!=0:
				cur.execute(query,args)
			else:
				i=i+1
		conn.commit()
		cur.close()
		conn.close()
		return ""

#Validation of testcase upload
def validateString(testCaseItem):
	if not testCaseItem: 
		return " "
	return testCaseItem

#Get test case details from Database and display in HTML page
def readTestCasesFromDB():
	conn = pymysql.connect(host=databasehost, user=databaseusername, passwd=databasepassword, port=3306, db=databasename)
	cur = conn.cursor()
	cur.execute("SELECT * FROM ivr_test_case_master")
	fileContent = """<html><title>IVR test case Execution</title><body><table border="1"><col width="180"><col width="380"><col width="280"><tr><th>Test Case ID</th><th>Test Case Step ID</th><th>Action </th> <th>Input Type </th> <th>Input Value </th><th>Pause </th> <th>Expected value</th><th>Prompt Duration </th><th>Actual Prompt</th><th>Confidence</th><th>Status</th><th>Recording URL</th><th>Recording duration</th></tr>"""
	for r in cur:
		fileContent =  fileContent + '<tr><td>'+validateString(r[0])+'</td><td>'+validateString(r[1])+'</td><td>'+validateString(r[2])+'</td><td>'+validateString(r[3])+'</td><td>'+validateString(r[4])+'</td><td>'+validateString(r[5])+'</td><td>'+validateString(r[6])+'</td><td>'+validateString(r[7])+'</td><td>'+validateString(r[8])+'</td><td>'+validateString(r[12])+'</td><td>'+validateString(r[10])+'</td><td>'+validateString(r[13])+'</td><td>'+validateString(r[14])+'</td></tr>'
		#print("r[1]|"+validateString(r[1])+"r[2]|"+validateString(r[2])+"r[3]|"+validateString(r[3])+"r[4]|"+validateString(r[4])+"r[5]|"+validateString(r[5])+"r[6]|"+validateString(r[6])+"r[7]|"+validateString(r[7])+"r[8]|"+validateString(r[8])+"r[9]|"+validateString(r[9]))
	cur.close()
	conn.close()
	fileContent = fileContent +'<form action="/ExecuteTestCase" method="post" enctype="multipart/form-data"><input type="submit" value="Execute Test cases" name="submit"></form></body></html>'
	return fileContent

# Submit POST request 
@app.route('/ExecuteTestCase',methods = ['POST'])
def ExecuteTestCaseUpdateResult():
	#i=0
	#jsonStringForTestCase=getJSONStringForTestCases()
	#print("jsonStringForTestCase==>"+jsonStringForTestCase)
	#request.args["TestCaseToBeExecuted"]=jsonStringForTestCase
	hostname = request.url_root
	print(hostname)
	return redirect(hostname + 'start', code=307)

#Create Json string of Testcase details and insert to table
def createJSONStringForTestCases():
	conn = pymysql.connect(host=databasehost, user=databaseusername, passwd=databasepassword, port=3306, db=databasename)
	cur = conn.cursor()
	cur.execute("SELECT testcaseid, action, input_type, input_value, pause_break FROM ivr_test_case_master")
	testCaseid=""
	testCaseStepsCount=""
	testCaseStepsList=[]
	i=0
	for r in cur:
		print("R0==>"+r[0]+"R1==>"+r[1]+"r[2]==>"+r[2]+"r[3]==>"+r[3]+"r[4]==>"+r[4])
		testCaseid=r[0]
		i=i+1
		testCaseStepsList.append(r[1]+"|"+r[2]+"|"+r[3]+"|"+r[4])
	testCaseStepsCount=i
	print("testCaseid==>"+testCaseid)
	print("testCaseStepsCount==>"+str(testCaseStepsCount))
	print(testCaseStepsList)
	jsonTestCaseString='{'+'"test_case_id":"'+testCaseid+'","test_steps":"'+str(testCaseStepsCount)+'","steps":['
	for testCaseStepItem in testCaseStepsList:
		testCaseStepItem=testCaseStepItem.replace('"','')
		splittedTestCaseItem=testCaseStepItem.split("|")
		jsonTestCaseString=jsonTestCaseString+'{"action":"'+splittedTestCaseItem[0]+'","input_type":"'+splittedTestCaseItem[1]+'","input_value":"'+splittedTestCaseItem[2]+'","pause":"'+splittedTestCaseItem[3]+'"},'
	jsonTestCaseString=jsonTestCaseString[:-1]
	jsonTestCaseString=jsonTestCaseString+']}'
	query = "INSERT INTO ivr_test_case_json(test_case_id, test_case_json) values (%s,%s)"
	args = (testCaseid,jsonTestCaseString)
	cur.execute(query,args)
	conn.commit()
	cur.close()
	conn.close()
	return ""

# Read test case details as string from database
def getJSONStringForTestCases():
	conn = pymysql.connect(host=databasehost, user=databaseusername, passwd=databasepassword, port=3306, db=databasename)
	cur = conn.cursor()
	cur.execute("SELECT * FROM ivr_test_case_json")
	for r in cur:
		print("Test case ID from DB==>"+r[0])
		print("Test case JSON from DB==>"+r[1])
		Test_case_details=r[1]
	cur.close()
	conn.close()
	return Test_case_details

# Show testcase execution result in HTML page
def ReturnTestCaseHTMLResult(testCaseIDToBePublished):	
	conn = pymysql.connect(host=databasehost, user=databaseusername, passwd=databasepassword, port=3306, db=databasename)
	cur = conn.cursor()
	cur.execute("SELECT * FROM ivr_test_case_master")
	fileContent = """<html><title>IVR test case Execution Result</title><body><table border="1"><col width="180"><col width="380"><col width="280"><tr><th>Test Case ID</th><th>Test Case Step ID</th><th>Action </th> <th>Input Type </th> <th>Input Value </th><th>Pause </th> <th>Expected value</th><th>Prompt Duration </th><th>Actual Prompt</th><th>Confidence</th><th>Status</th><th>Recording URL</th><th>Recording duration</th></tr>"""
	for r in cur:
		fileContent =  fileContent + '<tr><td>'+validateString(r[0])+'</td><td>'+validateString(r[1])+'</td><td>'+validateString(r[2])+'</td><td>'+validateString(r[3])+'</td><td>'+validateString(r[4])+'</td><td>'+validateString(r[5])+'</td><td>'+validateString(r[6])+'</td><td>'+validateString(r[7])+'</td><td>'+validateString(r[8])+'</td><td>'+validateString(r[12])+'</td><td>'+validateString(r[10])+'</td><td>'+validateString(r[13])+'</td><td>'+validateString(r[14])+'</td></tr>'
		print("R3==>"+r[3])
	cur.close()
	conn.close()
	fileContent = fileContent + '</body></html>'
	return fileContent

#########################################Twilio recording code#############################################
#Receive the POST request
@app.route('/start', methods=['GET','POST'])
def start():
	# Get testcase details as string
	session['testCaseObject'] = getJSONStringForTestCases()
	session['currentCount']=0
	currentStepCount=0
	testCaseObject = session['testCaseObject']
	testCaseJSON = json.loads(testCaseObject)
	test_case_id = testCaseJSON["test_case_id"]
	dnis = testCaseJSON["steps"][currentStepCount]["input_value"]
	print(dnis, cli)
	client = Client(account_sid, auth_token)
	call = client.calls.create(to=dnis, from_=cli, url=url_for('.record_welcome', test_case_id=[test_case_id], _external=True))
	return ""

# Record Welcome prompt
@app.route("/record_welcome", methods=['GET', 'POST'])
def record_welcome():
	response = VoiceResponse()
	currentTestCaseid=request.values.get("test_case_id", None)
	print("Reccalbackurl=> " + url_for('.recording_stat', step=[1], currentTestCaseID=[currentTestCaseid], _scheme='https', _external=True))
	response.record(trim="trim-silence", action="/recording?StepNumber=1", timeout="3", playBeep="false", recordingStatusCallback=url_for('.recording_stat', step=[1], currentTestCaseID=[currentTestCaseid], _scheme='https', _external=True),recordingStatusCallbackMethod="POST")
	return str(response)

# Twilio/Signalwire functions for record and TTS
@app.route("/recording", methods=['GET', 'POST'])
def recording():
	response = VoiceResponse()
	currentStepCount= request.values.get("StepNumber", None)
	print("CurrentStepCount is " + currentStepCount)
	testCaseObject = getJSONStringForTestCases()
	print ("testCaseObject==>"+currentStepCount)
	testCaseJSON = json.loads(testCaseObject)
	currentTestCaseid = testCaseJSON["test_case_id"]
	print ("Test Case ID ==>"+currentTestCaseid)
	action = testCaseJSON["steps"][int(currentStepCount)]["action"]
	print("Action is =>" + action)
	input_type = testCaseJSON["steps"][int(currentStepCount)]["input_type"]
	print("Input Type is =>" + input_type)
	input_value = testCaseJSON["steps"][int(currentStepCount)]["input_value"]
	print("Input Value is =>" + input_value)
	pause = testCaseJSON["steps"][int(currentStepCount)]["pause"]
	if pause!="":
		response.pause(length=int(pause))
		print("I have paused")
	if "Reply" in action:
		if "DTMF" in input_type:
			print("i am at DTMF input step")
			currentStepCount=int(currentStepCount)+1
			session['currentCount']=str(currentStepCount)
			response.play(digits=input_value)
			response.record(trim="trim-silence", action="/recording?StepNumber="+str(currentStepCount), timeout="3", playBeep="false", recordingStatusCallback=url_for('.recording_stat', step=[str(currentStepCount)], currentTestCaseID=[currentTestCaseid], _scheme='https', _external=True),recordingStatusCallbackMethod="POST")
		if "Say" in input_type:
			print("i am at Say input step")
			currentStepCount=int(currentStepCount)+1
			session['currentCount']=str(currentStepCount)
			response.say(input_value, voice="alice", language="en-US")
			response.record(trim="trim-silence", action="/recording?StepNumber="+str(currentStepCount), timeout="3", playBeep="false", recordingStatusCallback=url_for('.recording_stat', step=[str(currentStepCount)], currentTestCaseID=[currentTestCaseid], _scheme='https', _external=True),recordingStatusCallbackMethod="POST")
	if "Hangup" in action:
		response.hangup()
	return str(response)

# Receive recordng metadata
@app.route("/recording_stat", methods=['GET', 'POST'])
def recording_stat():
	print("I am at recording callback event")
	req = request.get_json(silent=True, force=True)
	StepNumber = request.values.get("step", None)
	print("StepNumber==>"+str(StepNumber))
	testCaseID = request.values.get("currentTestCaseID", None)
	print("testCaseID==>"+str(testCaseID))
	AccountSid = request.values.get("AccountSid", None)
	CallSid =  request.values.get("CallSid", None)
	RecordingSid = request.values.get("RecordingSid", None)
	RecordingUrl = request.values.get("RecordingUrl", None)
	RecordingStatus = request.values.get("RecordingStatus", None)
	RecordingDuration = request.values.get("RecordingDuration", None)
	RecordingChannels = request.values.get("RecordingChannels", None)
	RecordingStartTime = request.values.get("RecordingStartTime", None)
	RecordingSource	= request.values.get("RecordingSource", None)
	Recognized_text = goog_speech2text(RecordingUrl)
	#updateResultToDB(RecordingUrl, RecordingDuration, testCaseID, StepNumber)
	updateResultToDB(RecordingUrl, Recognized_text, testCaseID, StepNumber)
	print("testCaseID==>"+str(testCaseID))
	print ("RecordingUrl==>"+RecordingUrl+"\nRecognizedText==>"+Recognized_text+"\nStep number==>"+str(StepNumber))
	return ""

# This function calls Google STT and then returns recognition as text
#@app.route('/goog_speech2text', methods=['GET', 'POST'])
def goog_speech2text(RecordingUrl):
	#Generate Google STT Credentials
	service_account_info = json.loads(credentials_dgf)
	credentials = service_account.Credentials.from_service_account_info(service_account_info)
	# Create Google STT client
	client = speech.SpeechClient(credentials=credentials)
	#Create temporary file
	audiofileNameSplit = RecordingUrl.split("/")
	audiofile = audiofileNameSplit[len(audiofileNameSplit)-1]
	urllib.request.urlretrieve(RecordingUrl, audiofile)
	#Pass the audio to be recognized by Google Speech-To-Text
	with io.open(audiofile, 'rb') as audio_file:
		content = audio_file.read()
	audio = speech.types.RecognitionAudio(content=content)
	#Set the configuration parameters of the audio file for Google STT
	config = speech.types.RecognitionConfig(
		encoding=speech.enums.RecognitionConfig.AudioEncoding.LINEAR16,
		sample_rate_hertz=8000,
		language_code='en-US',
		# Enhanced models are only available to projects that opt in for audio data collection
        	use_enhanced=True,
		# Specify the model for the enhanced model usage.
		model='phone_call')
	#Get the response from Google STT	
	response = client.recognize(config, audio)
	for result in response.results:
		print('Transcript: {}'.format(result.alternatives[0].transcript))
		recognized_text = result.alternatives[0].transcript
	
	#This is for getting alternatives from recognized result
	#for i, result in enumerate(response.results):
        #alternative = result.alternatives[0]
	#print('-' * 20)
        #print('First alternative of result {}'.format(i))
        #print('Transcript: {}'.format(alternative.transcript))
	
	return recognized_text
	
# Update recording metadata to Database
def updateResultToDB(recordingURL,recognizedText,testcaseID,testCaseStep):
	conn = pymysql.connect(host=databasehost, user=databaseusername, passwd=databasepassword, port=3306, db=databasename)
	cur = conn.cursor()
	print(str(recordingURL)+"||"+str(recognizedText)+"||"+testcaseID+"||"+testCaseStep)
	query = "UPDATE ivr_test_case_master set recording_url = %s, actual_value = %s where testcaseid=%s and testcasestepid = %s"
	args = (recordingURL,str(recognizedText),str(testcaseID),testCaseStep)
	cur.execute(query,args)
	print("Rows Affected==>"+str(cur.rowcount))
	conn.commit()
	cur.close()
	conn.close()
	return ""
		
if __name__ == '__main__':
	port = int(os.getenv('PORT', 5000))
	print ('Starting app on port %d' % port)
	app.run(debug=False, port=port, host='0.0.0.0')