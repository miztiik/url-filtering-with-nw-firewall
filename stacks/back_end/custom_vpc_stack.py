from aws_cdk import aws_ec2 as _ec2
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


class CustomVpcStack(core.Stack):

    def __init__(
        self,
        scope: core.Construct,
        construct_id: str,
        stack_log_level: str,
        from_vpc_name=None,
        ** kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        id_prefix_str = f"miztiikNwFirewall"

        # Build VPC
        self.vpc = _ec2.CfnVPC(
            self,
            f"{id_prefix_str}Vpc",
            cidr_block='10.0.0.0/16',
            enable_dns_hostnames=True,
            enable_dns_support=True,
            instance_tenancy=None,
            tags=[{"key": "Name", "value": f"{id_prefix_str}Vpc"}]
        )

        # Internet Gateway
        igw = _ec2.CfnInternetGateway(
            self,
            f"{id_prefix_str}Igw",
            tags=[{"key": "Name", "value": f"{id_prefix_str}Igw"}]
        )

        # VPC Gateway Attachment
        vpc_gateway_attachment = _ec2.CfnVPCGatewayAttachment(
            self,
            f"{id_prefix_str}IgwVpcAttachment",
            vpc_id=self.vpc.ref,
            internet_gateway_id=igw.ref
        )

        azs = core.Fn.get_azs()

        # Firewall Subnets
        self.fw_subnet_01 = _ec2.CfnSubnet(
            self,
            f"{id_prefix_str}FwSubnet01",
            cidr_block="10.0.0.0/24",
            vpc_id=self.vpc.ref,
            assign_ipv6_address_on_creation=None,
            availability_zone=core.Fn.select(0, azs),
            ipv6_cidr_block=None,
            map_public_ip_on_launch=True,
            tags=[{"key": "Name", "value": f"{id_prefix_str}FwSubnet01"}]
        )

        self.fw_subnet_02 = _ec2.CfnSubnet(
            self,
            f"{id_prefix_str}FwSubnet02",
            cidr_block="10.0.1.0/24",
            vpc_id=self.vpc.ref,
            assign_ipv6_address_on_creation=None,
            availability_zone=core.Fn.select(1, azs),
            ipv6_cidr_block=None,
            map_public_ip_on_launch=True,
            tags=[{"key": "Name", "value": f"{id_prefix_str}FwSubnet02"}]
        )
        self.app_subnet_01 = _ec2.CfnSubnet(
            self,
            f"{id_prefix_str}AppSubnet01",
            cidr_block="10.0.2.0/24",
            vpc_id=self.vpc.ref,
            assign_ipv6_address_on_creation=None,
            availability_zone=core.Fn.select(0, azs),
            ipv6_cidr_block=None,
            map_public_ip_on_launch=True,
            tags=[{"key": "Name", "value": f"{id_prefix_str}AppSubnet01"}]
        )

        self.app_subnet_02 = _ec2.CfnSubnet(
            self,
            f"{id_prefix_str}AppSubnet02",
            cidr_block="10.0.3.0/24",
            vpc_id=self.vpc.ref,
            assign_ipv6_address_on_creation=None,
            availability_zone=core.Fn.select(1, azs),
            ipv6_cidr_block=None,
            map_public_ip_on_launch=True,
            tags=[{"key": "Name", "value": f"{id_prefix_str}AppSubnet02"}]
        )

        db_subnet_01 = _ec2.CfnSubnet(
            self,
            f"{id_prefix_str}DbSubnet01",
            cidr_block="10.0.4.0/24",
            vpc_id=self.vpc.ref,
            assign_ipv6_address_on_creation=None,
            availability_zone=core.Fn.select(0, azs),
            ipv6_cidr_block=None,
            map_public_ip_on_launch=True,
            tags=[{"key": "Name", "value": f"{id_prefix_str}DbSubnet01"}]
        )

        db_subnet_02 = _ec2.CfnSubnet(
            self,
            f"{id_prefix_str}DbSubnet02",
            cidr_block="10.0.5.0/24",
            vpc_id=self.vpc.ref,
            assign_ipv6_address_on_creation=None,
            availability_zone=core.Fn.select(1, azs),
            ipv6_cidr_block=None,
            map_public_ip_on_launch=True,
            tags=[{"key": "Name", "value": f"{id_prefix_str}DbSubnet02"}]
        )

        ################################################
        #########         ROUTE TABLES         #########
        ################################################


        # Route Table for Internet Gateway
        self.igw_rtb = _ec2.CfnRouteTable(
            self,
            f"{id_prefix_str}IgwRtb",
            vpc_id=self.vpc.ref,
            tags=[{"key": "Name", "value": f"{id_prefix_str}IgwRtb"}]
        )

        # Firewall Route Table
        fw_rtb = _ec2.CfnRouteTable(
            self,
            f"{id_prefix_str}FwRtb",
            vpc_id=self.vpc.ref,
            tags=[{"key": "Name", "value": f"{id_prefix_str}FwRtb"}]
        )

        # App Route Table
        self.app_rtb_az_a = _ec2.CfnRouteTable(
            self,
            f"AppAzARtb",
            vpc_id=self.vpc.ref,
            tags=[{"key": "Name", "value": f"{id_prefix_str}AppAzARtb"}]
        )
        self.app_rtb_az_b = _ec2.CfnRouteTable(
            self,
            f"AppAzBRtb",
            vpc_id=self.vpc.ref,
            tags=[{"key": "Name", "value": f"{id_prefix_str}AppAzBRtb"}]
        )

        # Db Route Table
        db_rtb = _ec2.CfnRouteTable(
            self,
            f"{id_prefix_str}DbRtb",
            vpc_id=self.vpc.ref,
            tags=[{"key": "Name", "value": f"{id_prefix_str}DbRtb"}]
        )

        ##########################################
        #########         ROUTES         #########
        ##########################################

        # FW to Internet Route
        fw_route_01 = _ec2.CfnRoute(
            self,
            f"{id_prefix_str}FwToIgwRoute",
            destination_cidr_block="0.0.0.0/0",
            route_table_id=fw_rtb.ref,
            gateway_id=igw.ref
        )

        # edge association
        igw_rtb_edge_assoc_rtb = _ec2.CfnGatewayRouteTableAssociation(
            self,
            f"{id_prefix_str}IgwIncomeRouteTableAssociation",
            gateway_id=igw.ref,
            route_table_id=self.igw_rtb.ref
        )


        # App to Internet Route
        """
        app_route_az_a_01 = _ec2.CfnRoute(
            self,
            f"{id_prefix_str}AppAzAToIgwRoute",
            destination_cidr_block="0.0.0.0/0",
            route_table_id=self.app_rtb_az_a.ref,
            gateway_id=igw.ref
        )

        app_route_az_b_01 = _ec2.CfnRoute(
            self,
            f"{id_prefix_str}AppAzBToIgwRoute",
            destination_cidr_block="0.0.0.0/0",
            route_table_id=self.app_rtb_az_b.ref,
            gateway_id=igw.ref
        )
        """

        # Attach Fw Subnet to FW Route Table
        fw_subnet_01_to_rtb = _ec2.CfnSubnetRouteTableAssociation(
            self,
            f"FwSubnet01ToRtb",
            route_table_id=fw_rtb.ref,
            subnet_id=self.fw_subnet_01.ref
        )
        fw_subnet_02_to_rtb = _ec2.CfnSubnetRouteTableAssociation(
            self,
            f"FwSubnet02ToRtb",
            route_table_id=fw_rtb.ref,
            subnet_id=self.fw_subnet_02.ref
        )


        # Attach App Subnet to App Route Table
        app_subnet_01_to_rtb = _ec2.CfnSubnetRouteTableAssociation(
            self,
            f"AppSubnet01ToRtb",
            route_table_id=self.app_rtb_az_a.ref,
            subnet_id=self.app_subnet_01.ref
        )
        app_subnet_02_to_rtb = _ec2.CfnSubnetRouteTableAssociation(
            self,
            f"AppSubnet02ToRtb",
            route_table_id=self.app_rtb_az_b.ref,
            subnet_id=self.app_subnet_02.ref
        )

        # Attach Db Subnet to Db Route Table
        db_subnet_01_to_rtb = _ec2.CfnSubnetRouteTableAssociation(
            self,
            f"DbSubnet01ToRtb",
            route_table_id=db_rtb.ref,
            subnet_id=db_subnet_01.ref
        )
        db_subnet_02_to_rtb = _ec2.CfnSubnetRouteTableAssociation(
            self,
            f"DbSubnet02ToRtb",
            route_table_id=db_rtb.ref,
            subnet_id=db_subnet_02.ref
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

    # properties to share with other stacks
    @property
    def get_vpc(self) -> _ec2.Vpc:
        return self.vpc
