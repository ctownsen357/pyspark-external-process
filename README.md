## pyspark-external-process
These scripts were used to run a 100,000 year simulation on 50 x 32 core Amazon EC2 instances utilizing S3 for permanent storage and a bash script to automatically initialize
each worker node.  The Apache Spark Python job:
* Creates an RDD of 100,000 years
* Breaks the RDD up into chunks of 50
* Distributes the RDD to the compute nodes
* Each compute node:
  * Creates a run-time folder
  * Creates a run-time control file
  * Copies the binary and control file to the run-time folder
  * Runs the simulation
  * Zips the results
  * Copies the results to an Amazon S3 bucket

### Setup
* Tested on Ubuntu 14 and RHEL/CentOS 7.x.
* Used the included init.sh (on Ubuntu) script to automatically configure each worker node by adding the script to the "User Data" section of Step 3: "Configure Instance Details" when setting up the EC2 instances
* My setup was very specific, download ~ 50 GB of input data, the program to be iteratively run, and a template control file, however the init script demonstrates how something like that may be accomplished and it could be modified to perform any initialization you need to do.

*Note:* My experience has been that the aws command line tool is MUCH faster than the s3cmd utility.  I use the aws command line tool in my bash init script and it copied, to each machine, ~ 50 GB of data to each worker machine in ~ 5 minutes - fast! I use S3cmd when downloading data from outside the Amazon AWS network because it is a very convenient utility.

### Running
*runproc.py* is the Spark Python job that I used to run the external process, zip the results and store the results out on Amazon S3.
The command to run is the typical way one would submit a spark job (from the spark directory):
```bash
./bin/spark-submit --master spark://ip-your-aws-machine-ip:7077 ./runproc.py
```

