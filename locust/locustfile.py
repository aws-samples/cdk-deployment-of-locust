# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import os
import string
import random
from locust import HttpUser, task, between

class MyLocust(HttpUser):
    host = "http://dummy"
    wait_time = between(1, 2)
    @task(100)
    def test(self):
        self.client.get("/")
