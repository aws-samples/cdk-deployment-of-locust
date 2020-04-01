# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import os
import string
import random
from locust import HttpLocust, TaskSet, task, between

class MyTaskSet(TaskSet):
    # This task will 15 times for every 1000 runs of the above task
    @task(15)
    def about(self):
        self.client.get("/blog")

class MyLocust(HttpLocust):
    host = "http://dummy"
    task_set = MyTaskSet
    wait_time = between(1, 2)
