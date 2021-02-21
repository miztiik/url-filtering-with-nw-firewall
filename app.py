#!/usr/bin/env python3

from aws_cdk import core

from url_filtering_with_nw_firewall.url_filtering_with_nw_firewall_stack import UrlFilteringWithNwFirewallStack


app = core.App()
UrlFilteringWithNwFirewallStack(app, "url-filtering-with-nw-firewall")

app.synth()
