this stack creates locust cluster for load testing

# contexts
- vpcid:  required, id of the vpc to create the test cluster in
- instancetype: optional, ec2 instance type to use in the cluster, default to c5.large
- clustersize: optional, locust test cluster size, if set to 1, standalone mode will be used, otherwise master/slave mode will be used, default to 3

example
```
cdk deploy -c vpcid=vpc-xxxxxxxx
```
