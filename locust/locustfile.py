# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import os
import string
import random
from locust import HttpLocust, TaskSet, task, between

class MyTaskSet(TaskSet):
    @task(100)
    def test(self):
        self.client.get("/Prod/test")

class MyLocust(HttpLocust):
    host = "http://dummy"
    host = "https://0r3nqio2fh.execute-api.ap-southeast-1.amazonaws.com"
    task_set = MyTaskSet
    wait_time = between(1, 2)
