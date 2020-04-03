# Welcome to the CDK deployment of Locust for load testing!

# Overview 
this stack creates locust cluster for load testing
## Architecture diagram

# Prerequisite
Install AWS CDK following the doc
https://docs.aws.amazon.com/cdk/latest/guide/getting_started.html

# How to run load test
## Setup
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

At this point you can now synthesize the CloudFormation template for this code.

```
$ cdk synth
```

Deploy
```
$ cdk deploy
```

Expected result & run load test:

# Cleanup


# More configs
- vpcid (required): id of the vpc to create the test cluster in
- instancetype (optional): ec2 instance type to use in the cluster, default to c5.large
- clustersize (optional): locust test cluster size, if set to 1, standalone mode will be used, otherwise master/slave mode will be used, default to 3
- locust_version (optional): locust version to deploy, default is 0.13.5
- no_web_ui (optional): run the locust cluster with or without web UI, default to False (with web UI)
- locust_user_number (optional): number of locust users to run in the load test, default is 100
- locust_hatch_rate (optional): number of users to hatch every second, default to 10

example
```
cdk deploy -c vpcid=vpc-xxxxxxxx
```

# Useful CDK commands
 * `cdk ls`          list all stacks in the app
 * `cdk synth`       emits the synthesized CloudFormation template
 * `cdk deploy`      deploy this stack to your default AWS account/region
 * `cdk diff`        compare deployed stack with current state
 * `cdk docs`        open CDK documentation