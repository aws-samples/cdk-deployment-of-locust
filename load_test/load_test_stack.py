# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

from aws_cdk import (
    core,
    aws_ec2 as ec2,
    aws_s3 as s3,
    aws_s3_deployment as s3deploy,
    aws_iam as iam,
)


class LoadTestStack(core.Stack):
    
    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)
        
        self.get_context()
        
        self.asset_bucket = self.prepare_s3_assets()
        
        self.create_ec2_cluster()
        
        core.CfnOutput(self, "LocustAddress",
            value=self.master.instance_public_dns_name,
            description="The address of the locust master instance", 
            export_name="LocustAddress"
        )
        
    def get_context(self):
        # get context
        self.vpcid = self.node.try_get_context("vpcid")
        self.instancetype = ec2.InstanceType(self.node.try_get_context("instancetype"))
        self.clustersize = int(self.node.try_get_context("clustersize"))
        self.locust_version = self.node.try_get_context("locust_version")
        self.no_web_ui = (self.node.try_get_context("no_web_ui") == "True")
        self.locust_user_number = int(self.node.try_get_context("locust_user_number"))
        self.locust_hatch_rate = int(self.node.try_get_context("locust_hatch_rate"))
        
    def get_userdata(self, is_master):
        # generate the ec2 userdata required
        userdata = ec2.UserData.for_linux()
        
        userdata.add_commands("""
                sudo yum -y install python-pip gcc
                sudo python -m pip install locustio==%s
                aws s3 cp s3://%s/locustfile.py .
            """ % (self.locust_version, self.asset_bucket.bucket_name))
        
        # generate run command depends on the different mode
        run_command = ""
        # User data for master
        if is_master:
            # with web UI
            if not self.no_web_ui:
                # if there's only one instance, no need to run in master slave mode
                run_command = "sudo locust -P 80 -f locustfile.py %s" % ("--master" if self.clustersize > 1 else "")
            # without web UI
            else:
                if self.clustersize > 1:
                    run_command = "sudo locust --no-web -c %s -r %s -f locustfile.py --expect-slaves %s" % (self.locust_user_number, self.locust_hatch_rate, self.clustersize - 1)
                else:
                    run_command = "sudo locust --no-web -c %s -r %s -f locustfile.py" % (self.locust_user_number, self.locust_hatch_rate)
        # user data for slave
        else:
            # with web UI
            if not self.no_web_ui:
                run_command = "sudo locust -f locustfile.py --slave --master-host %s" % (self.master.instance_private_ip)
            # without web UI
            else:
                run_command = "sudo locust -f locustfile.py --slave --master-host %s" % (self.master.instance_private_ip)
        userdata.add_commands(run_command)
        
        return userdata

    def create_ec2_cluster(self):
        # search for existing vpc
        vpc = ec2.Vpc.from_lookup(self, "VPC",
            vpc_id=self.vpcid
        )
        
        # use amazon linux 2
        ami = ec2.AmazonLinuxImage(
            generation=ec2.AmazonLinuxGeneration.AMAZON_LINUX_2,
            edition=ec2.AmazonLinuxEdition.STANDARD,
            storage=ec2.AmazonLinuxStorage.GENERAL_PURPOSE
        )
        
        # create ec2 role 
        role = iam.Role(self, "MyRole",
            assumed_by=iam.ServicePrincipal("ec2.amazonaws.com")
        )
        # give access to read s3 asset
        self.asset_bucket.grant_read(role);
        
        # master user data
        master_userdata = self.get_userdata(True)
        
        # master security group
        master_sg = ec2.SecurityGroup(self, "MasterSecurityGroup",
            vpc=vpc,
            allow_all_outbound=True
        )
        master_sg.add_ingress_rule(ec2.Peer.any_ipv4(), ec2.Port.tcp(80), "allow locust port")
        master_sg.add_ingress_rule(ec2.Peer.any_ipv4(), ec2.Port.tcp(22), "allow ssh")
        
        # create master node
        self.master = ec2.Instance(self, "Master", 
            instance_type=self.instancetype, 
            vpc=vpc, 
            instance_name="locust-master",
            machine_image=ami,
            security_group=master_sg,
            user_data=master_userdata,
            role=role,
        )
        
        # create slave nodes
        if self.clustersize > 1:
            # slave user data
            slave_userdata = self.get_userdata(False)
            
            # slave security group
            slave_sg = ec2.SecurityGroup(self, "SlaveSecurityGroup",
                vpc=vpc,
                allow_all_outbound=True
            )
            slave_sg.add_ingress_rule(ec2.Peer.any_ipv4(), ec2.Port.tcp(22), "allow ssh")
            master_sg.add_ingress_rule(slave_sg, ec2.Port.tcp(5557), "allow slave connection")
            
            # create slaves one by one
            for i in range(self.clustersize - 1):
                ec2.Instance(self, "Slave%s" % i, 
                    instance_type=self.instancetype, 
                    vpc=vpc, 
                    instance_name="locust-slave%s" % i,
                    machine_image=ami,
                    security_group=slave_sg,
                    user_data=slave_userdata,
                    role=role,
                )
                
        
    def prepare_s3_assets(self):
        asset_bucket = s3.Bucket(self, "AssetBucket")

        s3deploy.BucketDeployment(self, "DeployAsset",
            sources=[s3deploy.Source.asset("./locust")],
            destination_bucket=asset_bucket,
        )
        
        return asset_bucket
