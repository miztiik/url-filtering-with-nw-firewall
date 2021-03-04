from aws_cdk import aws_ec2 as _ec2
from aws_cdk import aws_iam as _iam
from aws_cdk import core


class GlobalArgs():
    """
    Helper to define global statics
    """

    OWNER = "MystiqueAutomation"
    ENVIRONMENT = "production"
    REPO_NAME = "url-filtering-with-nw-firewall"
    SOURCE_INFO = f"https://github.com/miztiik/{REPO_NAME}"
    VERSION = "2020_02_21"
    MIZTIIK_SUPPORT_EMAIL = ["mystique@example.com", ]


class PublicWorkloadOnEc2Stack(core.Stack):

    def __init__(
        self,
        scope: core.Construct,
        construct_id: str,
        vpc,
        app_subnet_01,
        app_subnet_02,
        ec2_instance_type: str,
        stack_log_level: str,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Read BootStrap Script):
        try:
            with open("stacks/back_end/public_workload_on_ec2/bootstrap_scripts/deploy_app.sh",
                      encoding="utf-8",
                      mode="r"
                      ) as f:
                user_data = _ec2.UserData.for_linux()
                user_data.add_commands(f.read())
        except OSError as e:
            print("Unable to read UserData script")
            raise e

        # Get the latest AMI from AWS SSM
        linux_ami = _ec2.AmazonLinuxImage(
            generation=_ec2.AmazonLinuxGeneration.AMAZON_LINUX_2)

        # Get the latest ami
        amzn_linux_ami = _ec2.MachineImage.latest_amazon_linux(
            generation=_ec2.AmazonLinuxGeneration.AMAZON_LINUX_2
        )

        # ec2 Instance Role
        _instance_role = _iam.Role(
            self,
            "webAppClientRole",
            assumed_by=_iam.ServicePrincipal(
                "ec2.amazonaws.com"),
            managed_policies=[
                _iam.ManagedPolicy.from_aws_managed_policy_name(
                    "AmazonSSMManagedInstanceCore"
                )
            ]
        )

        # Allow CW Agent to create Logs
        _instance_role.add_to_policy(_iam.PolicyStatement(
            actions=[
                "logs:Create*",
                "logs:PutLogEvents"
            ],
            resources=["arn:aws:logs:*:*:*"]
        ))

        # Allow Access to ElasticSearch Domain
        # https://docs.aws.amazon.com/elasticsearch-service/latest/developerguide/es-ac.html#es-ac-types-resource
        _instance_role.add_to_policy(_iam.PolicyStatement(
            actions=[
                "es:Describe*",
                "es:List*",
                "es:ESHttpPost",
                "es:ESHttpPut",
            ],
            resources=["*"]
        ))

        # Allow CW Agent to create Logs
        _instance_role.add_to_policy(_iam.PolicyStatement(
            actions=[
                "logs:Create*",
                "logs:PutLogEvents"
            ],
            resources=["arn:aws:logs:*:*:*"]
        ))

        # Instance Profile
        secured_public_workload_instance_profile = _iam.CfnInstanceProfile(
            self,
            "securedPublicWorkloadInstanceProfile",
            roles=[_instance_role.role_name]
        )

        # Security Group
        secured_public_workload_sg = _ec2.CfnSecurityGroup(
            self,
            "securedPublicWorkloadSG",
            vpc_id=vpc.ref,
            group_description="Allow Web Traffic to WebServer",
            group_name="securedPublicWorkloadSG",
            security_group_ingress=[
                _ec2.CfnSecurityGroup.IngressProperty(
                    ip_protocol="tcp",
                    cidr_ip="0.0.0.0/0",
                    from_port=80,
                    to_port=80,
                    description="Port 80 Traffic"
                ),
                _ec2.CfnSecurityGroup.IngressProperty(
                    ip_protocol="tcp",
                    cidr_ip="0.0.0.0/0",
                    from_port=443,
                    to_port=443,
                    description="Port 443 Traffic"
                )
            ]
        )

        self.secured_public_workload = _ec2.CfnInstance(
            self,
            "securedPublicWorkload",
            iam_instance_profile=secured_public_workload_instance_profile.ref,
            image_id=_ec2.MachineImage.latest_amazon_linux(
                generation=_ec2.AmazonLinuxGeneration.AMAZON_LINUX_2
            ).get_image(self).image_id,
            instance_type=f"{ec2_instance_type}",
            security_group_ids=[secured_public_workload_sg.ref],
            subnet_id=app_subnet_01.ref,
            user_data=core.Fn.base64(user_data.render()),
            tags=[core.CfnTag(key="Name", value=f"securedPublicWorkload")]
        )

        ###########################################
        ################# OUTPUTS #################
        ###########################################
        output_0 = core.CfnOutput(
            self,
            "AutomationFrom",
            value=f"{GlobalArgs.SOURCE_INFO}",
            description="To know more about this automation stack, check out our github page."
        )
        output_1 = core.CfnOutput(
            self,
            "PublicWorkloadPrivateIp",
            value=f"http://{self.secured_public_workload.attr_private_ip}",
            description=f"Private IP of Fluent Bit Server on EC2"
        )

        output_2 = core.CfnOutput(
            self,
            "PublicWorkloadInstance",
            value=(
                f"https://console.aws.amazon.com/ec2/v2/home?region="
                f"{core.Aws.REGION}"
                f"#Instances:search="
                f"{self.secured_public_workload.ref}"
                f";sort=instanceId"
            ),
            description=f"Login to the instance using Systems Manager and use curl to access the Instance"
        )

        output_3 = core.CfnOutput(
            self,
            "WebServerUrl",
            value=f"{self.secured_public_workload.attr_public_dns_name}",
            description=f"Public IP of Web Server on EC2"
        )

    # properties to share with other stacks
    @ property
    def get_inst_id(self):
        return self.secured_public_workload.instance_id
