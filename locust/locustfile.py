# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import os
import string
import random
from locust import HttpLocust, TaskSet, task, between

class MyTaskSet(TaskSet):
    @task(100)
    def test(self):
        self.client.get("/test")

class MyLocust(HttpLocust):
    host = "http://dummy"

    task_set = MyTaskSet
    wait_time = between(1, 2)
