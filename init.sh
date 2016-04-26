#!/bin/bash

#Init script to setup an Ubuntu AMI (preconfigured with Apache Spark 1.6.0):
# sets up directory
# copies necessary run-time data files and program from S3 to local directories (~ 50 GB of data in my case)
# starts the Apache Spark slave process pointing at the master node


#These are required to be set for an Amazon EC2 instance to be able to use the AWS commands correctly.
#For some reason that I haven't determined yet, the preconfigured settings in .aws/configure were not usable until AFTER the init step
#This gets around that problem
export AWS_ACCESS_KEY_ID=YourAWSAccessKeyID
export AWS_SECRET_ACCESS_KEY=YourAWSSecretKey
export region=us-east-1 #your region
export output=json

cd /home/ubuntu/ #ubuntu in this case but should be whatever user you want - or not needed if you won't be changing anything

#this was a helpful way to wait until the network connection for the worker node was completely available, I'm simply trying to download a file and sleeping for 2 seconds until that is completed
#prior to this the machines were unable to download data from S3 as the custom AWS EC2 init routine runs in parallel to the general machine init processes
while [ ! -f /tmp/sectest ]; do
        aws s3 --region us-east-1 cp s3://your.s3.bucket/sparkworker_init.sh  /tmp/sectest
        sleep 2
done

#chained these commands together so that if any one fails then the Spark worker process won't start - did this in the event some of the data did not copy over correctly or a configuration step failed
sudo chown ubuntu /mnt &&
mkdir /your/target-path &&
aws s3 --region us-east-1 cp s3://your.s3.bucket/some-folder/ /your/target-path/ --recursive && #In my case copied ~ 50GB of input data
chmod a+x /your/target-path/template/your-program && #make the binary executable
cd /home/ubuntu/spark-1.6.0-bin-hadoop2.6/ &&
sudo chown ubuntu:ubuntu /your/target-path -R && #so it may be run and accessed by the Spark process without admin privs
./sbin/start-slave.sh spark://your-master-ip:7077
