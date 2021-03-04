from aws_cdk import core
from aws_cdk import aws_ec2 as _ec2
from aws_cdk import aws_networkfirewall as _netfw
from aws_cdk import aws_logs as _logs


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


class UrlFilteringWithNwFirewallStack(core.Stack):

    def __init__(
        self,
        scope: core.Construct,
        construct_id: str,
        vpc,
        fw_subnet_01,
        fw_subnet_02,
        app_subnet_01,
        app_subnet_02,
        igw_rtb,
        app_rtb_az_a,
        app_rtb_az_b,
        stack_log_level: str,
        ** kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # The code that defines your stack goes here

        # Statics
        # Set Rule Group Capacity
        net_fw_capacity = 500
        id_prefix_str = f"miztiikNwFirewall"

        # Network Firewall Rule Group

        self.net_fw_stateless_rule_grp_01 = _netfw.CfnRuleGroup.RuleGroupProperty(
            rule_variables=None,
            rules_source=_netfw.CfnRuleGroup.RulesSourceProperty(
                rules_source_list=None,
                stateful_rules=None,
                stateless_rules_and_custom_actions=_netfw.CfnRuleGroup.StatelessRulesAndCustomActionsProperty(
                    stateless_rules=[
                        _netfw.CfnRuleGroup.StatelessRuleProperty(
                            priority=10,
                            rule_definition=[
                                _netfw.CfnRuleGroup.RuleDefinitionProperty(
                                    actions=["aws:forward_to_sfe"],
                                    match_attributes=_netfw.CfnRuleGroup.MatchAttributesProperty(
                                        destination_ports=[
                                            _netfw.CfnRuleGroup.PortRangeProperty(
                                                from_port=80,
                                                to_port=80
                                            ),
                                            _netfw.CfnRuleGroup.PortRangeProperty(
                                                from_port=443,
                                                to_port=443
                                            )
                                        ],
                                        destinations=[
                                            _netfw.CfnRuleGroup.AddressProperty(
                                                address_definition="0.0.0.0/0"
                                            )
                                        ],
                                        sources=[
                                            _netfw.CfnRuleGroup.AddressProperty(
                                                address_definition="10.0.0.0/16"
                                            )
                                        ],
                                        source_ports=[
                                            _netfw.CfnRuleGroup.PortRangeProperty(
                                                from_port=0,
                                                to_port=65535
                                            )
                                        ]
                                    )
                                )
                            ]
                        )
                    ]
                )
            )
        )

        # Create Network Firewall rule group Stateful

        # Rule to ALLOW Domains
        self.net_fw_stateful_rule_grps_01 = _netfw.CfnRuleGroup(
            self,
            "webFilterNetworkFirewallStatefulRuleGrp01",
            capacity=net_fw_capacity,
            rule_group_name=f"ALLOW-For-Domains",
            type="STATEFUL",
            description="Miztiik Automation: Network Firewall Stateful Rule Group - ALLOW",
            rule_group=_netfw.CfnRuleGroup.RuleGroupProperty(
                rule_variables=None,
                rules_source=_netfw.CfnRuleGroup.RulesSourceProperty(
                        rules_source_list=_netfw.CfnRuleGroup.RulesSourceListProperty(
                            generated_rules_type="ALLOWLIST",
                            targets=["aws.com", "google.com"],
                            target_types=["HTTP_HOST"]
                        )
                )
            )
        )

        # Rule to DENY Domains
        self.net_fw_stateful_rule_grps_02 = _netfw.CfnRuleGroup(
            self,
            "webFilterNetworkFirewallStatefulRuleGrp02",
            capacity=net_fw_capacity,
            rule_group_name=f"DENY-For-Domains",
            type="STATEFUL",
            description="Miztiik Automation: Network Firewall Stateful Rule Group - DENY",
            rule_group=_netfw.CfnRuleGroup.RuleGroupProperty(
                rule_variables=None,
                rules_source=_netfw.CfnRuleGroup.RulesSourceProperty(
                    rules_source_list=_netfw.CfnRuleGroup.RulesSourceListProperty(
                        generated_rules_type="DENYLIST",
                        targets=[
                            ".example.com",
                            ".modi-am-i.com"
                        ],
                        target_types=["HTTP_HOST"]
                    )
                )
            )
        )

        # SURICATA RULE
        # DENY based on url
        # drop tcp any any -> any any (msg:"Miztiik Drop tcp traffic"; content:"NoGo"; sid:130381; rev:1;)

        self.net_fw_stateful_rule_grps_03 = _netfw.CfnRuleGroup(
            self,
            "webFilterNetworkFirewallStatefulRuleGrp03",
            capacity=net_fw_capacity,
            rule_group_name=f"DENY-On-Url",
            type="STATEFUL",
            description="Miztiik Automation: Network Firewall Stateful Rule Group - DENY on content 'deny_test'",
            rule_group=_netfw.CfnRuleGroup.RuleGroupProperty(
                rule_variables=None,
                rules_source=_netfw.CfnRuleGroup.RulesSourceProperty(
                    rules_string='drop tcp any any -> any any (msg:"Miztiik Drop tcp traffic"; content:"NoGo"; sid:130381; rev:1;)',
                    rules_source_list=None
                )
            )
        )

        # Create firewall policy
        net_fw_policy = _netfw.CfnFirewallPolicy(
            self,
            "webFilterNetworkFirewallPolicy",
            firewall_policy_name=f"{construct_id}Policy",
            firewall_policy=_netfw.CfnFirewallPolicy.FirewallPolicyProperty(
                # stateless_default_actions=_netfw.CfnFirewallPolicy.FirewallPolicyProperty.StatelessDefaultActions(stateless_actions=["aws:pass"]),
                stateless_default_actions=["aws:forward_to_sfe"],
                stateless_fragment_default_actions=["aws:forward_to_sfe"],
                stateful_rule_group_references=[
                    _netfw.CfnFirewallPolicy.StatefulRuleGroupReferenceProperty(
                        resource_arn=self.net_fw_stateful_rule_grps_01.attr_rule_group_arn
                    ),
                    _netfw.CfnFirewallPolicy.StatefulRuleGroupReferenceProperty(
                        resource_arn=self.net_fw_stateful_rule_grps_02.attr_rule_group_arn
                    )
                ]
            )
        )

        self.net_firewall = _netfw.CfnFirewall(
            self,
            "webFilterNetworkFirewall",
            firewall_name=f"{construct_id}",
            firewall_policy_arn=net_fw_policy.attr_firewall_policy_arn,
            subnet_mappings=[_netfw.CfnFirewall.SubnetMappingProperty(subnet_id=fw_subnet_01.ref),
                             _netfw.CfnFirewall.SubnetMappingProperty(subnet_id=fw_subnet_02.ref)],
            vpc_id=vpc.ref,
            description=f"Miztiik Automation: Web Filtering Using AWS Network Firewall",
            delete_protection=False,
            firewall_policy_change_protection=False,
            subnet_change_protection=False,
        )

        # Add Firewall Logging

        # Create Custom Loggroup for Firewall
        net_firewall_alerts_lg_name = "nw-fw-alerts-01"
        net_firewall_flow_lg_name = "nw-fw-flow-01"

        net_firewall_alerts_lg = _logs.LogGroup(
            self,
            "webFilterNetworkFirewallAlertsLogGroup",
            log_group_name=f"{net_firewall_alerts_lg_name}",
            removal_policy=core.RemovalPolicy.DESTROY,
            retention=_logs.RetentionDays.ONE_DAY
        )
        net_firewall_flow_lg = _logs.LogGroup(
            self,
            "webFilterNetworkFirewallFlowLogGroup",
            log_group_name=f"{net_firewall_flow_lg_name}",
            removal_policy=core.RemovalPolicy.DESTROY,
            retention=_logs.RetentionDays.ONE_DAY
        )

        net_firewall_log = _netfw.CfnLoggingConfiguration(
            self,
            "webFilterNetworkFirewallLog",
            firewall_arn=self.net_firewall.attr_firewall_arn,
            logging_configuration=_netfw.CfnLoggingConfiguration.LoggingConfigurationProperty(
                log_destination_configs=[
                    _netfw.CfnLoggingConfiguration.LogDestinationConfigProperty(
                        log_destination={
                            "logGroup": net_firewall_alerts_lg_name},
                        log_destination_type="CloudWatchLogs",
                        log_type="ALERT"
                    ),
                    _netfw.CfnLoggingConfiguration.LogDestinationConfigProperty(
                        log_destination={
                            "logGroup": net_firewall_flow_lg_name},
                        log_destination_type="CloudWatchLogs",
                        log_type="FLOW"
                    )
                ]
            )
        )

        # Update Routing Table
        az_a_fw_endpoint = f"{core.Fn.select(1, core.Fn.split(':', core.Fn.select(0, self.net_firewall.attr_endpoint_ids)))}"
        az_b_fw_endpoint = f"{core.Fn.select(1, core.Fn.split(':', core.Fn.select(1, self.net_firewall.attr_endpoint_ids)))}"

        # Update Internet Gateway to route through firewall Endpoints to Subnets
        igw_to_app_subnet_01 = _ec2.CfnRoute(
            self,
            f"{id_prefix_str}IgwToAppAzARoute",
            route_table_id=igw_rtb.ref,
            vpc_endpoint_id=az_a_fw_endpoint,
            destination_cidr_block=app_subnet_01.cidr_block,
        )
        igw_to_app_subnet_02 = _ec2.CfnRoute(
            self,
            f"{id_prefix_str}IgwToAppAzBRoute",
            route_table_id=igw_rtb.ref,
            vpc_endpoint_id=az_b_fw_endpoint,
            destination_cidr_block=app_subnet_02.cidr_block,
        )

        # Update App Subnet to route through Internet Traffic through firewall Endpoints
        app_subnet_01_to_igw = _ec2.CfnRoute(
            self,
            f"{id_prefix_str}AppAzAToIgwRoute",
            route_table_id=app_rtb_az_a.ref,
            vpc_endpoint_id=az_a_fw_endpoint,
            destination_cidr_block="0.0.0.0/0"
        )
        app_subnet_02_to_igw = _ec2.CfnRoute(
            self,
            f"{id_prefix_str}AppAzBToIgwRoute",
            route_table_id=app_rtb_az_b.ref,
            vpc_endpoint_id=az_b_fw_endpoint,
            destination_cidr_block="0.0.0.0/0"
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
            "NetworkFirewallEndpoints1",
            value=f"{az_a_fw_endpoint}",
            description="Network Firewall Endpoints: 1"
        )
        output_2 = core.CfnOutput(
            self,
            "NetworkFirewallEndpoints2",
            value=f"{az_b_fw_endpoint}",
            description="Network Firewall Endpoints: 2"
        )
