""" This script demonstrates how to use Apache Spark to:
- Run external processes on an Apache Spark cluster
- Zip the results of the output
- Store results out on Amazon S3 """

import sys
import os
from operator import add
from shutil import copyfile
import subprocess
import shutil
#may need  to install these via pip or easy_install on your worker nodes
import zipfile
import boto

from pyspark import SparkContext

def zipdir(path, ziph):
""" zips all the files in the specified directory """
    # ziph is zipfile handle
	for root, dirs, files in os.walk(path):
		for file in files:
			ziph.write(os.path.join(root, file),file,zipfile.ZIP_DEFLATED)

def copy_to_s3(file_to_copy,filename):
""" copies the specified file over to a pre-configured S3 bucket """
	awsKeyId = "YourAWSKeyId"
	awsSecretKey = "YourAWSSecretKey"
	region = "us-east-1" #your region

	s3 = boto.connect_s3(awsKeyId, awsSecretKey)

	bucket = s3.get_bucket("your.s3.bucket") #should mod to make this a parameter
	key = bucket.new_key('process_results/' + filename) #this is where you'll store the results, mod to take as parameter
	key.set_contents_from_filename(file_to_copy)

def runProcess(recs):
""" 
	runProcess: 
	- Takes a set of records from the RDD(years to be simulated in blocks of 50 in my use case)
	- For each rec/block of 50 years
		*Creates a run folder for the simulation
		*Creats a control file for the legacy program indicating a start and end year for the simulation 
		*Copies the statically compiled program and writes the control file to the simulation folder
		*Runs the simulation
		*Zip the output (used zip as the consumer of the data required zip)
"""


	
	root_dir = '/mnt/your_path/template/'

	for rec in recs:
		return_part = []
		start_track = min(rec)
		end_track = max(rec)

		track_name = str(start_track) + "_" + str(end_track)
		working_dir = os.path.join(root_dir,track_name)

		with open(os.path.join(root_dir, "control-file.ctl")) as infile, open(os.path.join(working_dir, "control-file.ctl"), 'w') as outfile:
			if not os.path.exists(working_dir):
				os.makedirs(working_dir)
				shutil.copy(os.path.join(root_dir, "a-program-name"), os.path.join(working_dir, "a-program-name"))

				replacements = {'StartYear':start_track, 'EndYear':end_track}

				for line in infile:
					for src, target in replacements.iteritems():
						line = line.replace(src, str(target))
					outfile.write(line)

		rc = subprocess.call([os.path.join(working_dir, 'a-program-name'), 'control-file.ctl'],cwd=working_dir)

		zipf = zipfile.ZipFile(os.path.join(root_dir,track_name + '.zip'), 'w')
		zipdir(working_dir, zipf)
		zipf.close()
		copy_to_s3(os.path.join(root_dir,track_name + '.zip'),track_name + '.zip') 
		shutil.rmtree(working_dir)
		os.remove(os.path.join(root_dir,track_name + '.zip'))

		return_part.append( (track_name, start_track,end_track, rc) )
		return iter(return_part) #in my case I wasn't interested in doing anything post-process but one could easilly add a step here to read the output data for further processing in Spark


def chunks(l, n):
    """Yield successive n-sized chunks from l. Used to break by list of years up into chunks within the RDD"""
    for i in xrange(0, len(l), n):
        yield l[i:i+n]

if __name__ == "__main__":
	"""
		Usage: Runs a simulation program in parallel by generating a unique control file
	"""
	sc = SparkContext(appName="YourAppName")
	print('starting...')
	split_count = 50
	simulation_count = 100001#add 1 due to indexing
	data = list(range(1,simulation_count))
	sub_lists = list(chunks(data, split_count))
	rdd = sc.parallelize(sub_lists,len(sub_lists)) 
	rslt_collect = rdd.mapPartitions(runFortran).collect()

	for x in rslt_collect:
		print("{tn} - {stat}".format(tn=x[0], stat=x[3]))

	sc.stop()

