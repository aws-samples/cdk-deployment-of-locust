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
        
        asset_bucket = self.prepare_s3_assets()
        
        master = self.create_ec2_cluster(asset_bucket)
        
        core.CfnOutput(self, "LocustAddress",
            value=master.instance_public_dns_name,
            description="The address of the locust master instance", 
            export_name="LocustAddress"
        )

    def create_ec2_cluster(self, asset_bucket):
        # get context
        vpcid = self.node.try_get_context("vpcid")
        instancetype = ec2.InstanceType(self.node.try_get_context("instancetype"))
        clustersize = int(self.node.try_get_context("clustersize"))
        locust_version = self.node.try_get_context("locust_version")
        
        # search for existing vpc
        vpc = ec2.Vpc.from_lookup(self, "VPC",
            vpc_id=vpcid
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
        asset_bucket.grant_read(role);
        
        # master user data
        mode = "--master" if clustersize > 1 else ""
        master_userdata = ec2.UserData.for_linux()
        master_userdata.add_commands("""
            sudo yum -y install python-pip gcc
            sudo python -m pip install locustio==%s
            aws s3 cp s3://%s/locustfile.py .
            sudo locust -P 80 -f locustfile.py %s
        """ % (locust_version, asset_bucket.bucket_name, mode))
        
        # master security group
        master_sg = ec2.SecurityGroup(self, "MasterSecurityGroup",
            vpc=vpc,
            allow_all_outbound=True
        )
        master_sg.add_ingress_rule(ec2.Peer.any_ipv4(), ec2.Port.tcp(80), "allow locust port")
        master_sg.add_ingress_rule(ec2.Peer.any_ipv4(), ec2.Port.tcp(22), "allow ssh")
        
        # create master node
        master = ec2.Instance(self, "Master", 
            instance_type=instancetype, 
            vpc=vpc, 
            instance_name="locust-master",
            machine_image=ami,
            security_group=master_sg,
            user_data=master_userdata,
            role=role,
        )
        
        # create slave nodes
        if clustersize > 1:
            # slave user data
            slave_userdata = ec2.UserData.for_linux()
            slave_userdata.add_commands("""
                sudo yum -y install python-pip gcc
                sudo python -m pip install locustio==%s
                aws s3 cp s3://%s/locustfile.py .
                sudo locust -f locustfile.py --slave --master-host %s
            """ % (locust_version, asset_bucket.bucket_name, master.instance_private_ip))
            
            # slave security group
            slave_sg = ec2.SecurityGroup(self, "SlaveSecurityGroup",
                vpc=vpc,
                allow_all_outbound=True
            )
            slave_sg.add_ingress_rule(ec2.Peer.any_ipv4(), ec2.Port.tcp(22), "allow ssh")
            master_sg.add_ingress_rule(slave_sg, ec2.Port.tcp(5557), "allow slave connection")
            
            # create slaves one by one
            for i in range(clustersize - 1):
                ec2.Instance(self, "Slave%s" % i, 
                    instance_type=instancetype, 
                    vpc=vpc, 
                    instance_name="locust-slave%s" % i,
                    machine_image=ami,
                    security_group=slave_sg,
                    user_data=slave_userdata,
                    role=role,
                )
                
        return master
        
        
        
    def prepare_s3_assets(self):
        asset_bucket = s3.Bucket(self, "AssetBucket")

        s3deploy.BucketDeployment(self, "DeployAsset",
            sources=[s3deploy.Source.asset("./locust")],
            destination_bucket=asset_bucket,
        )
        
        return asset_bucket
