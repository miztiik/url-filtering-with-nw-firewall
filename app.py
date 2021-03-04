#!/usr/bin/env python3

from aws_cdk import core

from stacks.back_end.vpc_stack import VpcStack
from stacks.back_end.custom_vpc_stack import CustomVpcStack
from stacks.back_end.public_workload_on_ec2.public_workload_on_ec2_stack import PublicWorkloadOnEc2Stack
from stacks.back_end.url_filtering_with_nw_firewall.url_filtering_with_nw_firewall_stack import UrlFilteringWithNwFirewallStack


app = core.App()


# VPC Stack for hosting Secure API & Other resources
vpc_stack = CustomVpcStack(
    app,
    f"{app.node.try_get_context('project')}-vpc-stack",
    stack_log_level="INFO",
    description="Miztiik Automation: Custom Multi-AZ VPC"
)
# Deploy public facing workload on EC2
public_workload_on_ec2 = PublicWorkloadOnEc2Stack(
    app,
    f"secured-workload-on-ec2-stack",
    vpc=vpc_stack.vpc,
    app_subnet_01=vpc_stack.app_subnet_01,
    app_subnet_02=vpc_stack.app_subnet_02,
    ec2_instance_type="t2.micro",
    stack_log_level="INFO",
    description="Miztiik Automation: Deploy public facing workload on EC2"
)

# Produce Customer Info Messages
url_filtering_with_nw_firewall = UrlFilteringWithNwFirewallStack(
    app,
    f"{app.node.try_get_context('project')}-stack",
    vpc=vpc_stack.vpc,
    fw_subnet_01=vpc_stack.fw_subnet_01,
    fw_subnet_02=vpc_stack.fw_subnet_02,
    app_subnet_01=vpc_stack.app_subnet_01,
    app_subnet_02=vpc_stack.app_subnet_02,
    igw_rtb=vpc_stack.igw_rtb,
    app_rtb_az_a=vpc_stack.app_rtb_az_a,
    app_rtb_az_b=vpc_stack.app_rtb_az_b,
    stack_log_level="INFO",
    description="Miztiik Automation: Web Filtering Using AWS Network Firewall"
)


# Stack Level Tagging
_tags_lst = app.node.try_get_context("tags")

if _tags_lst:
    for _t in _tags_lst:
        for k, v in _t.items():
            core.Tags.of(app).add(k, v, apply_to_launched_instances=True)


app.synth()
