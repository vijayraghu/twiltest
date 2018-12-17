import os
import sys
import requests
import json
from flask import Flask, request, Response, make_response, jsonify, url_for, redirect, session
# Twilio Helper Library
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Record, Gather, Say, Dial
import pymysql

# Declare global variables
#asr_lang = os.environ["asr_lang"]
#cli = os.environ["cli"]

#Initiate Flask app
app = Flask(__name__)

#Set Secret Key for session variables
SECRET_KEY = os.environ.get("SECRET_KEY", default=None)
app.secret_key=SECRET_KEY

#Receive the POST request
@app.route('/start', methods=['GET','POST'])
def start():
	#Get testcase details as string
	session['testCaseObject'] = session['TestCaseString']
	print ("session['TestCaseString']==>"+session['TestCaseString'])
	session['currentCount']=0
	currentCount=0
	testCaseObject = session['testCaseObject']
	testCaseJSON = json.loads(testCaseObject)
	action="place_call"
	first_action = "place_call"
	if "place_call" in first_action:
		#dnis = testCaseJSON["steps"][currentCount][input]
		# Twilio Account Sid and Auth Token
		#account_sid = os.environ["account_sid"]
		account_sid = "ACf7d3b821a12be5e1b80f274db0b64aef"
		#auth_token = os.environ["auth_token"]
		auth_token = "ab0591b383511f41962c9c1217b7c5dd"
		client = Client(account_sid, auth_token)
		session['currentCount']=1
		call = client.calls.create(to="+917397340531", from_="+19362984573", url='http://a205bf3e.ngrok.io/recording?StepNumber=2')	
		#call = client.calls.create(to="+917397340531", from_="+19362984573")	
	else:
		print ("test case is not valid")
	return ""
  
  @app.route("/recording", methods=['GET', 'POST'])
def recording():
    response = VoiceResponse()
    #session['testCaseObject'] = """{"test_case_id":"TC103","test_steps":"5","steps": [{"action":"place_call", 		"input":"8888888"		},
	#{"action":"Say", 	"input":"i want my account balance"	},	{"action":"Say", 	"input":"savings account"	},	#{"action":"Say", 		"input":"12345678"		},		{"action":"Hangup", 		"input":""		}	]}"""
    currentStepCount= request.values.get("StepNumber", None)
    #testCaseObject="""{"test_case_id":"TC103","test_steps":"5","steps": [{"action":"place_call", 		#"input":"8888888"		},
	#{"action":"Say", 	"input":"i want my account balance"	},	{"action":"Say", 	"input":"savings account"	},	#{"action":"Say", 		"input":"12345678"		},		{"action":"Hangup", 		"input":""		}	]}"""
    session['testCaseObject']=getJSONStringForTestCases()
    testCaseObject=session['testCaseObject']
    print ("testCaseObject==>"+currentStepCount)
    testCaseJSON = json.loads(testCaseObject)
    print ("test_case_id==>"+testCaseJSON["test_case_id"])
    action = testCaseJSON["steps"][int(currentStepCount)]["action"]
    inputMsg = testCaseJSON["steps"][int(currentStepCount)]["input"]
    print("currentStepCount==>"+str(currentStepCount)+"")
    if action=='do_nothing':
	    currentStepCount=currentStepCount+1
	    session['currentCount']=str(currentStepCount)
	    response.record(maxLength="5", action="/recording?StepNumber="+str(currentStepCount),timeout="5",recordingStatusCallback="/recording_stat?Step="+str(currentStepCount)+"&currentTestCaseID="+testCaseJSON["test_case_id"])
    if "Say" in action:
	    currentStepCount=int(currentStepCount)+1
	    session['currentCount']=str(currentStepCount)
	    response.say(inputMsg)
	    response.record(maxLength="5", action="/recording?StepNumber="+str(currentStepCount),timeout="5",recordingStatusCallback="/recording_stat?Step="+str(currentStepCount)+"&currentTestCaseID="+testCaseJSON["test_case_id"])
    if "Hangup" in action:
	    response.hangup()
    return str(response)
    
   #####
##### Receive recordng metadata
#####
@app.route('/recording_stat', methods=['POST'])
def recording_stat():
	req = request.get_json(silent=True, force=True)
	AccountSid = request.values.get("AccountSid", None)
	CallSid =  request.values.get("CallSid", None)
	RecordingSid = request.values.get("RecordingSid", None)
	RecordingUrl = request.values.get("RecordingUrl", None)
	RecordingStatus = request.values.get("RecordingStatus", None)
	RecordingDuration = request.values.get("RecordingDuration", None)
	RecordingChannels = request.values.get("RecordingChannels", None)
	RecordingStartTime = request.values.get("RecordingStartTime", None)
	RecordingSource	= request.values.get("RecordingSource", None)
	StepNumber = request.values.get("Step", None)
	testCaseID = request.values.get("currentTestCaseID", None)
	print("testCaseID==>"+str(testCaseID))
	print ("RecordingSid==>"+RecordingSid+"\nRecordingUrl==>"+RecordingUrl+"\nRecordingDuration==>"+RecordingDuration+"\nStep number==>"+str(StepNumber))
	return ""
def getJSONStringForTestCases():
	conn = pymysql.connect(host='127.0.0.1', user='root', passwd='root', db='infypoc')
	cur = conn.cursor()
	cur.execute("SELECT * FROM ivr_test_case_master")
	testCaseid=""
	testCaseStepsCount=""
	testCaseStepsList=[]
	i=0
	for r in cur:
		print("R0==>"+r[0]+"R1==>"+r[1]+"r[2]==>"+r[2]+"r[3]==>"+r[3])
		testCaseid=r[0]
		i=i+1
		testCaseStepsList.append(r[1]+"|"+r[2]+"|"+r[3])
	testCaseStepsCount=i
	print("testCaseid==>"+testCaseid)
	print("testCaseStepsCount==>"+str(testCaseStepsCount))
	print(testCaseStepsList)
	jsonTestCaseString='{'+'"test_case_id":"'+testCaseid+'","test_steps":"'+str(testCaseStepsCount)+'","steps":['
	for testCaseStepItem in testCaseStepsList:
		testCaseStepItem=testCaseStepItem.replace('"','')
		splittedTestCaseItem=testCaseStepItem.split("|")
		jsonTestCaseString=jsonTestCaseString+'{"action":"'+splittedTestCaseItem[1]+'","input":"'+splittedTestCaseItem[2]+'"},'
	jsonTestCaseString=jsonTestCaseString[:-1]
	jsonTestCaseString=jsonTestCaseString+']}'
	return jsonTestCaseString
  
  if __name__ == '__main__':
	port = int(os.getenv('PORT', 5001))
	print ("Starting app on port %d" % port)
	app.run(debug=False, port=port, host='0.0.0.0')
