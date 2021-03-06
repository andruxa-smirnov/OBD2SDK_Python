import urllib2
import json
import time
from ConfigParser import *
import sqlite3
import jnsdk
import sys
import logging

c = ConfigParser()
c.read("config.txt")

WSURL = c.get("Settings", "url")
APIKey = jnsdk.APIKey()

#Buffer
db = c.get("Settings", "sqlite_gps_db")

#Sync utility. Pull records from buffer and push to API

#Server globals
WSURLConnectTest = WSURL

#Other Settings
CheckInterval = 10 #seconds
DisplayStatus = False
logging.basicConfig(filename="events.log", format='%(asctime)s %(levelname)s:%(message)s', level=logging.DEBUG)

#Check that there's a connection to the API server
def IsConnected(URL):
        try:
		urllib2.urlopen(URL)
	except urllib2.HTTPError, e:
                #print e.code
		if e.code == 403:
			return True #server's online, just not letting that directory be browsed
		return False
	except urllib2.URLError, e:
                #print e.args
		return False
	return True


while True:
	time.sleep(CheckInterval) #check for an internet connection to server every N seconds
	while IsConnected(WSURLConnectTest):

		#client = MongoClient()
		#db = client[mongodb]
		#coll = db[mongocollection]

		#i = coll.count()
	

		conn = sqlite3.connect(db)
		curs = conn.cursor()
		curs.execute("select count(*) from gps")
		row = curs.fetchone()
		i = row[0]
		conn.close()

		if DisplayStatus:
			#display # of records that are to be synced
			sys.stdout.write("Records to sync: " + str(i) + "\n")
			sys.stdout.flush()
		#logging.debug(str(i) + " records to sync")
	
		while i <> 0:

			if IsConnected(WSURLConnectTest):
				#get oldest record
				#Ideally start from oldest record, but this is a major performance hit as written currently. Removed it for now.
				#curs.execute("select lat, NS, lon, EW, eventdate, id from gps order by eventdate")
				conn = sqlite3.connect(db)
				curs = conn.cursor()	
				curs.execute("select lat, NS, lon, EW, eventdate, id from gps limit 1")
				row = curs.fetchone()
				conn.close()
				#Convert from dict data type retunred by coll.find() into a JSON list data type 
				#Also, remove the _ID item from the array as that's not needed when sending data to the API.
				id = row[5] 
				jarray = {"APIKey":APIKey, "lat":row[0], "NS":row[1], "lon":row[2], "EW":row[3], "EventDate":row[4]}
				jdata = json.dumps(jarray)
				#print "Uploading: " + jdata
				result = urllib2.urlopen(WSURL+"gpslog.php", jdata)
				r = result.read()
				if r == "true":
					#logging.debug("Record successfully uploaded to server: " + str(id))
					#confirm the record was received by checking the API's return code. If so, delete the record from Mongo
					conn = sqlite3.connect(db)
        	                        curs = conn.cursor()
					curs.execute("delete from gps where id = (?)", (id,))
					conn.commit()
					conn.close()
				else:
					#API isn't saving the data. Log or alert the system to this.
					logging.warning("Failed to upload GPS db row. ID=" + str(id) + "; Result=" + r)
					print "Failed to upload. ID="+str(id)+r
				conn = sqlite3.connect(db)
                                curs = conn.cursor()
				curs.execute("select count(*) from gps")
                                row = curs.fetchone()
                                i = row[0]
                                conn.close()
	
				if DisplayStatus:
                                	#Display sync status
                                        sys.stdout.write("\rRecords left: " + str(i))
                                        sys.stdout.flush()
	#jdata = {"APIKey":APIKey, "PID":PID, "PIDValue":PIDValue, "EventDate":"2014-01-01 12:00:00"}
	#client = MongoClient()
	#db = client[mongodb]
	#collection = db[mongocollection]
	#post_id = collection.insert(jdata)




