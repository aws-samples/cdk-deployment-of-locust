# Welcome to the CDK deployment of Locust for load testing!

# Overview 
This tool automatically creates configurable load testing for your wordloads. 
It supports both public workload or private workload.
The tool itself is built on CDK and Locust.(https://locust.io/)

## Architecture diagram
The below diagrams show how the architecture works in public mode and private mode.
![Public mode](/images/public_mode.png)
<br/>
<br/>
![Private mode](/images/private_mode.png)
A new VPC is always created to host the locust test clusters.

# How to Run Load Test
## Prerequisite
Install AWS CDK following the doc
https://docs.aws.amazon.com/cdk/latest/guide/getting_started.html

## Run with default settings
The `cdk.json` file tells the CDK Toolkit how to execute your app.

This project is set up like a standard Python project.  The initialization
process also creates a virtualenv within this project, stored under the .env
directory.  To create the virtualenv it assumes that there is a `python3`
(or `python` for Windows) executable in your path with access to the `venv`
package. If for any reason the automatic creation of the virtualenv fails,
you can create the virtualenv manually.

To manually create a virtualenv on MacOS and Linux:

```
$ python3 -m venv .env
```

After the init process completes and the virtualenv is created, you can use the following
step to activate your virtualenv.

```
$ source .env/bin/activate
```

If you are a Windows platform, you would activate the virtualenv like this:

```
% .env\Scripts\activate.bat
```

Once the virtualenv is activated, you can install the required dependencies.

```
$ pip install -r requirements.txt
```

Modify your locust load test configuration in locust/locustfile.py
Update host in the following code to the public application you want to test

```
host = "http://dummy"
```

At this point you can now synthesize the CloudFormation template for this code.

```
$ cdk synth
```

Deploy
```
$ cdk deploy
```

## Expected result
Default setup will spin a load test to test your public application. It creats a locust of 3(1 master, 2 slaves).
You will see progress in your console when the load testing cluster is automatically setup.
At the end, it outputs something like below
```
Outputs:
load-test.LocustAddress = ec2-xx-xx-xxx-xxx.region-x.compute.amazonaws.com
```
Visit the LocustAddress from the output, and start your loadtest in the web browser.
NOTE: After all the steps are finished, please wait for 3 minutes before you can visit the testing address.
It takes some time for the EC2 to bootstrap the locust application. 

## Cleanup
Destory the cluster
```
$ cdk destroy
```

# Advanced Configs
The tool can be configured in command line, for example
```
$ cdk deploy -c no_web_ui=True -c vpc_to_peer=vpc-xxxxxxxx -c vpc_to_peer_cidr=172.31.0.0/16
```

## Supported Parameters
### vpc_cidr (optional)
- cidr of the vpc created to run locust cluster. 
- Make sure it doesn't conflic with CIDR of VPC to peer, if you are testing internal workloads. 
- Default to 10.0.0.0/16
```
// to create the locust cluster in a VPC with CIDR 172.0.0.1/16
cdk deploy -c vpc_cidr=172.0.0.1/16
```

### instancetype (optional)
- ec2 instance type to use in the cluster
- default to c5.large
```
// use r5.large to run the locust cluster
cdk deploy -c instancetype=r5.large
``` 

### clustersize (optional)
- locust test cluster size
- if set to 1, standalone mode will be used, otherwise master/slave mode will be used
- default to 3
```
// run locust in non-cluster mode
cdk deploy -c clustersize=1

// run locust in a cluster of 4 slaves 1 master
cdk deploy -c clustersize=5
``` 

### locust_version (optional)
- locust version to deploy
- default is 0.13.5
```
// run locust version 0.11.1
cdk deploy -c locust_version=0.11.1
``` 

### no_web_ui (optional)
- run the locust cluster with or without web UI. 
- In UI mode, locust cluster will be configured into public subnets. In no UI mode, it will be put into private subnets. 
- default to False (with web UI)
```
// run locust without web UI, the test will automatically start itself
// locust cluster is set up in private subnet in this mode
cdk deploy -c no_web_ui=True

// run locust with web UI, you can access the UI via public address output 
// locust cluster is set up in public subnet in this mode
cdk deploy -c no_web_ui=False
``` 

### locust_user_number(optional)
- number of locust users to run in the load test
- this parameter only works in no_web_ui mode
- default is 100
```
// run locust in command mode, test will automatically start itself
// it will hatch 20 users per second until it reaches 200
cdk deploy -c no_web_ui=True -c locust_user_number=200 -c locust_hatch_rate=20
``` 

### locust_hatch_rate (optional)
- number of users to hatch every second
- this parameter only works in no_web_ui mode
- default to 10
```
// run locust in command mode, test will automatically start itself
// it will hatch 20 users per second until it reaches 200
cdk deploy -c no_web_ui=True -c locust_user_number=200 -c locust_hatch_rate=20
``` 

### vpc_to_peer (optional)
- vpc ID of the vpc to peer with the new VPC. 
- It needs to be used with vpc_to_peer_cidr. Normally it is where you workload to test lies. 
- default to an empty string 

```
// to run load test in private mode. 
// workload to test is running in VPC with ID vpc-xxxxxxx, it has a CIDR of 172.31.0.0/16
// VPC peer will be created between the target VPC and locust cluster VPC
// In no web UI mode, load test will automatically run without triggering from the web interface. 
cdk deploy -c vpc_to_peer=vpc-xxxxxxxx -c vpc_to_peer_cidr=172.31.0.0/16 -c no_web_ui=True 
``` 

### vpc_to_peer_cidr (optional)
- cidr of the vpc to peer. 
- It needs to be used with vpc_to_peer. 
- default to empty string
```
// to run load test in private mode. 
// workload to test is running in VPC with ID vpc-xxxxxxx, it has a CIDR of 172.31.0.0/16
// VPC peer will be created between the target VPC and locust cluster VPC
// In no web UI mode, load test will automatically run without triggering from the web interface.
cdk deploy -c vpc_to_peer=vpc-xxxxxxxx -c vpc_to_peer_cidr=172.31.0.0/16 -c no_web_ui=True 
``` 

## Write Your Own Locustfile 
Modify your locust load test configuration in locust/locustfile.py  
Please refer to https://docs.locust.io/en/stable/writing-a-locustfile.html for how to write locustfile

# Others
## Useful CDK commands
 * `cdk ls`          list all stacks in the app
 * `cdk synth`       emits the synthesized CloudFormation template
 * `cdk deploy`      deploy this stack to your default AWS account/region
 * `cdk diff`        compare deployed stack with current state
 * `cdk docs`        open CDK documentation


# License
This library is licensed under the MIT-0 License.See the LICENSE file.