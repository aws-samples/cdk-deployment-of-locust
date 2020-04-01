# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import setuptools


with open("README.md") as fp:
    long_description = fp.read()


setuptools.setup(
    name="cdk-deployment-of-locust",
    version="1.0",

    description="this is a sample code that uses aws cdk to build up a locust test cluster for easy load testing.",
    long_description=long_description,
    long_description_content_type="text/markdown",

    author="Andrew(Qingjie) Ren",

    package_dir={"": "load_test"},
    packages=setuptools.find_packages(where="load_test"),

    install_requires=[
        "aws-cdk.core",
        "aws-cdk.aws-ec2",
        "aws-cdk.aws-s3",
        "aws-cdk.aws-s3-deployment",
        "aws-cdk.aws-iam",
    ],

    python_requires=">=3.6",

    classifiers=[
        "Development Status :: 4 - Beta",

        "Intended Audience :: Developers",

        "License :: OSI Approved :: Apache Software License",

        "Programming Language :: JavaScript",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",

        "Topic :: Software Development :: Code Generators",
        "Topic :: Utilities",

        "Typing :: Typed",
    ],
)
