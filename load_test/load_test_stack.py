# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
import random

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
        
        if self.deploy_in_public_subnets:
            # output locust master instance info
            core.CfnOutput(self, "LocustAddress",
                value=self.master.instance_public_dns_name,
                description="The address of the locust master instance", 
                export_name="LocustAddress"
            )
        else:
            # output private address info
            core.CfnOutput(self, "LocustPrivateAddress",
                value=self.master.instance_private_dns_name,
                description="The private address of the locust master instance", 
                export_name="LocustPrivateAddress"
            )
        
    def get_context(self):
        # get context
        self.vpc_cidr = self.node.try_get_context("vpc_cidr")
        self.vpc_to_peer = self.node.try_get_context("vpc_to_peer")
        self.vpc_to_peer_cidr = self.node.try_get_context("vpc_to_peer_cidr")
        self.instancetype = ec2.InstanceType(self.node.try_get_context("instancetype"))
        self.clustersize = int(self.node.try_get_context("clustersize"))
        self.locust_version = self.node.try_get_context("locust_version")
        self.no_web_ui = (self.node.try_get_context("no_web_ui") == "True")
        self.locust_user_number = int(self.node.try_get_context("locust_user_number"))
        self.locust_hatch_rate = int(self.node.try_get_context("locust_hatch_rate"))
        # if no UI is required, create it in private subnets, # if ui is required, create it in public subnets
        self.deploy_in_public_subnets = not self.no_web_ui
        
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
        # create a new VPC
        vpc = ec2.Vpc(self, "TheVPC",
            cidr=self.vpc_cidr
        )
        
        # create vpc peering with existing vpc if needed
        if self.vpc_to_peer:
            self.create_vpc_peering(vpc)
            
        
        # get subnets to create locust cluster in
        if self.deploy_in_public_subnets:
            subnets = ec2.SubnetSelection(subnets=vpc.public_subnets)
        else:
            subnets = ec2.SubnetSelection(subnets=vpc.private_subnets)
                
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
            vpc_subnets=subnets,
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
                    vpc_subnets=subnets,
                )
                
        
    def prepare_s3_assets(self):
        asset_bucket = s3.Bucket(self, "AssetBucket")

        s3deploy.BucketDeployment(self, "DeployAsset",
            sources=[s3deploy.Source.asset("./locust")],
            destination_bucket=asset_bucket,
        )
        
        return asset_bucket
        
        
    def create_vpc_peering(self, vpc):
        # get peering vpc
        peering_vpc = ec2.Vpc.from_lookup(self, "PeeringVPC", vpc_id=self.vpc_to_peer)
        print(peering_vpc.public_subnets)
        # create vpc peering
        peering = ec2.CfnVPCPeeringConnection(self, "Peering", 
                            peer_vpc_id=self.vpc_to_peer, 
                            vpc_id=vpc.vpc_id)
        vpc_peering_id = peering.ref
        
        # create vpc peering routing
        self.add_peering_route(vpc, peering_vpc, vpc_peering_id, destination_cidr=self.vpc_to_peer_cidr)
        self.add_peering_route(peering_vpc, vpc, vpc_peering_id)
        
    
    def add_peering_route(self, vpc, destination_vpc, peering_id, destination_cidr=""):
        route_table_ids = set()
        # add public route table ids
        for subnet in vpc.public_subnets:
            route_table_ids.add(subnet.route_table.route_table_id)
        # add private route table ids
        for subnet in vpc.private_subnets:
            route_table_ids.add(subnet.route_table.route_table_id)
            
        for rt_id in route_table_ids:
            # if destination cidr doesn't have a forced value, use destination VPC's CIDR
            # this is here because IVpcProxy created from Vpc.from_lookup() doesn't support vpc_cidr_block yet 
            if not destination_cidr:
                destination_cidr = destination_vpc.vpc_cidr_block
            ec2.CfnRoute(self, 'PeerRoute%s' % random.getrandbits(32), route_table_id=rt_id, 
                        destination_cidr_block=destination_cidr, 
                        vpc_peering_connection_id=peering_id) 