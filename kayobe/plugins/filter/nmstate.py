# Copyright (c) 2026 StackHPC Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import re

import jinja2
from kayobe.plugins.filter import networks
from kayobe.plugins.filter import utils


def _get_ip_config(context, name, inventory_hostname, defroute=None):
    ip = networks.net_ip(context, name, inventory_hostname)
    bootproto = networks.net_bootproto(context, name, inventory_hostname)
    prefix = networks.net_prefix(context, name, inventory_hostname)

    config = {"enabled": False}
    if bootproto == "dhcp":
        config = {"enabled": True, "dhcp": True}
        if defroute is False:
            config["auto-routes"] = False
    elif ip:
        address = {"ip": ip}
        if prefix:
            address["prefix-length"] = int(prefix)
        config = {
            "enabled": True,
            "dhcp": False,
            "address": [address]
        }

    return config


# Ethtool feature aliases for user convenience (documented aliases only)
ETHTOOL_FEATURE_ALIASES = {
    'rx': 'rx-checksum',
    'gro': 'rx-gro',
    'gso': 'tx-generic-segmentation',
    'lro': 'rx-lro'
}

# Tier 1 supported ethtool features (most critical performance features)
TIER1_ETHTOOL_FEATURES = {
    'rx-checksum',              # Receive checksum offload
    'tx-checksum-ip-generic',   # Transmit checksum offload
    'rx-gro',                   # Generic Receive Offload
    'tx-generic-segmentation',  # Generic Segmentation Offload
    'rx-lro',                   # Large Receive Offload
    'hw-tc-offload'             # Hardware traffic control offload
}

# Supported ring buffer parameters
SUPPORTED_RING_PARAMS = {
    'rx', 'tx', 'rx-max', 'tx-max', 'rx-jumbo', 'rx-mini'
}

MAX_U32 = 2**32 - 1
MAX_VLAN_PRIORITY = 7


def _resolve_ethtool_feature_aliases(features):
    """Convert ethtool feature aliases to canonical names.

    Args:
        features (dict): Feature configuration with possible aliases

    Returns:
        dict: Features with aliases resolved to canonical names

    Raises:
        ValueError: If feature contains invalid values
    """
    if not isinstance(features, dict):
        raise ValueError("Ethtool features must be a dictionary")

    resolved = {}
    for key, value in features.items():
        if not isinstance(value, bool):
            raise ValueError(
                f"Ethtool feature '{key}' must be boolean, "
                f"got {type(value).__name__}")

        canonical_name = ETHTOOL_FEATURE_ALIASES.get(key, key)
        resolved[canonical_name] = value

    return resolved


def _validate_ethtool_features(features):
    """Validate ethtool features against Tier 1 supported features.

    Args:
        features (dict): Resolved feature configuration

    Returns:
        dict: Validated features

    Raises:
        ValueError: If unsupported features are specified
    """
    unsupported = set(features.keys()) - TIER1_ETHTOOL_FEATURES
    if unsupported:
        supported_list = ', '.join(sorted(TIER1_ETHTOOL_FEATURES))
        alias_list = ', '.join(
            f"{alias} -> {canonical}"
            for alias, canonical in ETHTOOL_FEATURE_ALIASES.items())
        raise ValueError(
            f"Unsupported ethtool features: {', '.join(sorted(unsupported))}. "
            f"Tier 1 supported features: {supported_list}. "
            f"Supported aliases: {alias_list}")

    return features


def _validate_ethtool_ring(ring_config):
    """Validate ethtool ring buffer configuration.

    Args:
        ring_config (dict): Ring buffer configuration

    Returns:
        dict: Validated ring configuration

    Raises:
        ValueError: If invalid ring parameters are specified
    """
    if not isinstance(ring_config, dict):
        raise ValueError("Ethtool ring configuration must be a dictionary")

    unsupported = set(ring_config.keys()) - SUPPORTED_RING_PARAMS
    if unsupported:
        supported_list = ', '.join(sorted(SUPPORTED_RING_PARAMS))
        raise ValueError(
            f"Unsupported ring parameters: {', '.join(sorted(unsupported))}. "
            f"Supported parameters: {supported_list}")

    # Validate values are positive integers
    for param, value in ring_config.items():
        if not isinstance(value, int) or value < 0:
            raise ValueError(
                f"Ring parameter '{param}' must be a non-negative integer, "
                f"got {value}")

    return ring_config


def _process_ethtool_config(ethtool_config):
    """Process structured ethtool configuration into nmstate format.

    Args:
        ethtool_config (dict): Structured ethtool configuration

    Returns:
        dict: nmstate-compatible ethtool configuration

    Raises:
        ValueError: If configuration is invalid
    """
    if not isinstance(ethtool_config, dict):
        raise ValueError("Ethtool configuration must be a dictionary")

    nmstate_ethtool = {}

    # Process ring buffer configuration
    if 'ring' in ethtool_config:
        validated_ring = _validate_ethtool_ring(ethtool_config['ring'])
        nmstate_ethtool['ring'] = validated_ring

    # Process feature configuration with alias resolution and validation
    if 'feature' in ethtool_config:
        features = ethtool_config['feature']
        resolved_features = _resolve_ethtool_feature_aliases(features)
        validated_features = _validate_ethtool_features(resolved_features)
        nmstate_ethtool['feature'] = validated_features

    return nmstate_ethtool


def _disable_ip_config(iface):
    iface["ipv4"] = {"enabled": False}
    iface["ipv6"] = {"enabled": False}


def _port_name(port):
    if isinstance(port, dict):
        return port.get("name")
    return port


def _default_iface_type(iface_name):
    # Match MichaelRigart.interfaces dummy_interface_regex: 'dummy.*'.
    if isinstance(iface_name, str) and re.match(r"dummy.*", iface_name):
        return "dummy"
    return "ethernet"


def _parse_route_options(context, name, index, route):
    supported_keys = {
        "cidr",
        "gateway",
        "metric",
        "onlink",
        "options",
        "src",
        "table",
    }
    unsupported_keys = sorted(set(route) - supported_keys)
    if unsupported_keys:
        raise ValueError(
            f"Network '{name}' has unsupported routing route keys at "
            f"index {index} for the nmstate engine: "
            f"{', '.join(unsupported_keys)}")

    route_config = {}

    if route.get("metric") is not None:
        route_config["metric"] = int(route["metric"])
    if route.get("src") is not None:
        route_config["source"] = route["src"]
    if route.get("onlink") is not None:
        route_config["on-link"] = utils.call_bool_filter(
            context, route["onlink"])

    options = route.get("options")
    if options is None:
        return route_config
    if not isinstance(options, list):
        raise ValueError(
            f"Network '{name}' has invalid routing route options format at "
            f"index {index} for the nmstate engine. Route options must be "
            "a list.")

    for option in options:
        if not isinstance(option, str):
            raise ValueError(
                f"Network '{name}' has invalid routing route option at "
                f"index {index} for the nmstate engine. Route options must "
                "be strings.")

        option_key = None
        option_value = None
        if option == "onlink":
            option_key = "on-link"
            option_value = True
        elif option.startswith("metric "):
            option_key = "metric"
            option_value = int(option.split(None, 1)[1])
        elif option.startswith("src "):
            option_key = "source"
            option_value = option.split(None, 1)[1]
        else:
            raise ValueError(
                f"Network '{name}' has unsupported routing route option at "
                f"index {index} for the nmstate engine: '{option}'")

        existing_value = route_config.get(option_key)
        if existing_value is not None and existing_value != option_value:
            raise ValueError(
                f"Network '{name}' has conflicting routing route option at "
                f"index {index} for the nmstate engine: '{option}'")
        route_config[option_key] = option_value

    return route_config


def _get_bond_options(context, name, inventory_hostname):
    bond_option_map = {
        "bond_ad_select": "ad_select",
        "bond_downdelay": "downdelay",
        "bond_lacp_rate": "lacp_rate",
        "bond_miimon": "miimon",
        "bond_updelay": "updelay",
        "bond_xmit_hash_policy": "xmit_hash_policy",
    }

    bond_options = {}
    for attr, option_name in bond_option_map.items():
        value = networks.net_attr(context, name, attr, inventory_hostname)
        if value is not None:
            bond_options[option_name] = value

    return bond_options


def _validate_vlan_qos_map_int(value, network_name, direction, field):
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(
            f"Network '{network_name}' has invalid {direction} QoS map "
            f"'{field}' value '{value}'. Expected an integer.")

    if value < 0 or value > MAX_U32:
        raise ValueError(
            f"Network '{network_name}' has invalid {direction} QoS map "
            f"'{field}' value '{value}'. Expected a value in range "
            f"0..{MAX_U32}.")

    if direction == "ingress" and field == "from" \
            and value > MAX_VLAN_PRIORITY:
        raise ValueError(
            f"Network '{network_name}' has invalid ingress QoS map "
            f"'from' value '{value}'. Maximum VLAN priority is "
            f"{MAX_VLAN_PRIORITY}.")

    if direction == "egress" and field == "to" \
            and value > MAX_VLAN_PRIORITY:
        raise ValueError(
            f"Network '{network_name}' has invalid egress QoS map "
            f"'to' value '{value}'. Maximum VLAN priority is "
            f"{MAX_VLAN_PRIORITY}.")

    return value


def _validate_vlan_qos_map_entry(entry, network_name, direction):
    if not isinstance(entry, dict):
        raise ValueError(
            f"Network '{network_name}' has invalid {direction} QoS map "
            "entry format. Expected a dict with keys 'from' and 'to'.")

    if "from" not in entry or "to" not in entry:
        raise ValueError(
            f"Network '{network_name}' has invalid {direction} QoS map "
            "entry. Required keys are 'from' and 'to'.")

    return {
        "from": _validate_vlan_qos_map_int(
            entry["from"], network_name, direction, "from"),
        "to": _validate_vlan_qos_map_int(
            entry["to"], network_name, direction, "to")
    }


def _validate_and_sort_vlan_qos_map(raw_map, network_name, direction):
    if raw_map is None:
        return None

    if not isinstance(raw_map, list):
        raise ValueError(
            f"Network '{network_name}' has invalid {direction} QoS map "
            f"format '{type(raw_map).__name__}'. Expected a list of dicts "
            "with keys 'from' and 'to'.")

    normalized = []
    for entry in raw_map:
        normalized.append(_validate_vlan_qos_map_entry(
            entry, network_name, direction))

    normalized.sort(key=lambda item: (item["from"], item["to"]))
    return normalized


def _get_vlan_qos_map(context, name, inventory_hostname, direction):
    qos_map = networks.net_attr(
        context, name, f"{direction}_qos_map", inventory_hostname)
    return _validate_and_sort_vlan_qos_map(qos_map, name, direction)


@jinja2.pass_context
def nmstate_config(context, names, inventory_hostname=None):
    interfaces = {}
    routes = []
    rules = []

    # Get routing table name to ID mapping
    route_tables_list = utils.get_hostvar(
        context, "network_route_tables", inventory_hostname)
    route_tables = {}
    if route_tables_list:
        route_tables = {table["name"]: table["id"]
                        for table in route_tables_list}

    def get_iface(name):
        if name not in interfaces:
            interfaces[name] = {"name": name, "state": "up"}
        return interfaces[name]

    for name in names:
        iface_name = networks.net_interface(context, name, inventory_hostname)
        if not iface_name:
            continue

        iface = get_iface(iface_name)

        mtu = networks.net_mtu(context, name, inventory_hostname)
        if mtu:
            iface["mtu"] = mtu

        # IP Configuration. nmstate supports multiple addresses, but Kayobe
        # usually defines one per network.
        defroute = networks.net_defroute(
            context, name, inventory_hostname)
        if defroute is not None:
            defroute = utils.call_bool_filter(context, defroute)

        ipv4_config = _get_ip_config(
            context, name, inventory_hostname, defroute)
        if ipv4_config.get("enabled"):
            if "ipv4" not in iface or not iface["ipv4"].get("enabled"):
                iface["ipv4"] = ipv4_config
            elif not ipv4_config.get("dhcp"):
                addresses = ipv4_config["address"]
                iface["ipv4"].setdefault("address", []).extend(
                    addresses)

        # Gateway - only add if defroute allows it
        gateway = networks.net_gateway(
            context, name, inventory_hostname)
        if gateway:
            # Respect defroute: only add default route if defroute
            # is None (default) or True
            if defroute is None or defroute:
                routes.append({
                    "destination": "0.0.0.0/0",
                    "next-hop-address": gateway,
                    "next-hop-interface": iface_name
                })

        # Routes and Rules
        net_routes = networks.net_routes(context, name, inventory_hostname)
        for i, route in enumerate(net_routes or []):
            if not isinstance(route, dict):
                raise ValueError(
                    f"Network '{name}' has invalid routing route format at "
                    f"index {i} for the nmstate engine. Routes must use dict "
                    "format. String format routes are only supported by the "
                    "default network engine.")
            route_config = {
                "destination": route["cidr"],
                "next-hop-address": route.get("gateway"),
                "next-hop-interface": iface_name,
            }
            route_config.update(
                _parse_route_options(context, name, i, route))
            table = route.get("table")
            if table is not None:
                # Look up table name in mapping, or use value if numeric
                table_id = route_tables.get(table, table)
                # Ensure table_id is an integer
                if isinstance(table_id, str):
                    if table_id.isdigit():
                        table_id = int(table_id)
                    else:
                        raise ValueError(
                            f"Routing table '{table}' is not defined in "
                            f"network_route_tables and is not a valid "
                            f"numeric table ID")
                route_config["table-id"] = int(table_id)
            routes.append(route_config)

        net_rules = networks.net_rules(context, name, inventory_hostname)
        for rule in net_rules or []:
            if not isinstance(rule, dict):
                raise ValueError(
                    f"Network '{name}' has invalid routing rule format for "
                    "the nmstate engine. Rules must use dict format "
                    "(keys: from, to, priority, table). String format rules "
                    "are only supported by the default network engine.")
            rule_config = {}

            if rule.get("from") is not None:
                rule_config["ip-from"] = rule["from"]
            if rule.get("to") is not None:
                rule_config["ip-to"] = rule["to"]

            priority_value = rule.get("priority")
            if priority_value is not None:
                rule_config["priority"] = int(priority_value)

            table = rule.get("table")
            if table is not None:
                # Look up table name in mapping, or use value if numeric
                table_id = route_tables.get(table, table)
                # Ensure table_id is an integer
                if isinstance(table_id, str):
                    if table_id.isdigit():
                        table_id = int(table_id)
                    else:
                        raise ValueError(
                            f"Routing table '{table}' is not defined in "
                            f"network_route_tables and is not a valid "
                            f"numeric table ID")
                rule_config["route-table"] = int(table_id)

            rules.append(rule_config)

        # Specific Interface Types
        if networks.net_is_bridge(context, name, inventory_hostname):
            iface["type"] = "linux-bridge"
            br_ports = networks.net_bridge_ports(
                context, name, inventory_hostname)
            stp = networks.net_bridge_stp(
                context, name, inventory_hostname)

            bridge_config = {}  # type: dict[str, object]
            bridge_config["port"] = [{"name": p} for p in br_ports or []]

            # Only configure STP when explicitly set
            if stp is not None:
                stp_enabled = stp == "true"
                bridge_config["options"] = {
                    "stp": {"enabled": stp_enabled}}
                iface["bridge"] = bridge_config
            else:
                iface["bridge"] = bridge_config

            # Ensure ports are initialized if not otherwise defined.
            # Check for explicit type configuration via
            # <network>_port_type_<portname>.
            for port in br_ports or []:
                port_iface = get_iface(port)
                if "type" not in port_iface:
                    # Check for explicit type configuration
                    port_type = networks.net_attr(
                        context, name, f"port_type_{port}",
                        inventory_hostname)
                    port_iface["type"] = (
                        port_type if port_type else _default_iface_type(port))

        elif networks.net_is_bond(context, name, inventory_hostname):
            iface["type"] = "bond"
            slaves = networks.net_bond_slaves(
                context, name, inventory_hostname)
            mode = networks.net_bond_mode(context, name, inventory_hostname)
            link_agg_config = {"port": slaves or []}
            if mode is not None:
                link_agg_config["mode"] = mode
            else:
                # nmstate requires bond mode. Provide a sensible default.
                # balance-rr (round-robin) works in most environments without
                # requiring switch configuration.
                link_agg_config["mode"] = "balance-rr"

            bond_options = _get_bond_options(
                context, name, inventory_hostname)
            if bond_options:
                link_agg_config["options"] = bond_options

            iface["link-aggregation"] = link_agg_config
            # Ensure slaves are initialized if not otherwise defined.
            # Check for explicit type configuration via
            # <network>_slave_type_<slavename>.
            for slave in slaves or []:
                slave_iface = get_iface(slave)
                if "type" not in slave_iface:
                    # Check for explicit type configuration
                    slave_type = networks.net_attr(
                        context, name, f"slave_type_{slave}",
                        inventory_hostname)
                    slave_iface["type"] = (
                        slave_type
                        if slave_type else _default_iface_type(slave))

        elif networks.net_is_vlan_interface(
                context, name, inventory_hostname):
            iface["type"] = "vlan"
            vlan_id = networks.net_vlan(
                context, name, inventory_hostname)
            parent = networks.net_parent(
                context, name, inventory_hostname)

            # Derive VLAN ID from interface name if not explicitly
            # set
            if vlan_id is None:
                vlan_match = re.match(
                    r"^[a-zA-Z0-9_\-]+\.([1-9][\d]{0,3})$",
                    iface_name)
                if vlan_match:
                    vlan_id = vlan_match.group(1)
                else:
                    # Skip VLAN config if we can't derive the ID
                    continue

            # Derive parent interface if not explicitly set
            if not parent:
                parent = re.sub(
                    r'\.{}$'.format(vlan_id), '', iface_name)

            iface["vlan"] = {
                "base-iface": parent,
                "id": int(vlan_id)
            }

            ingress_qos_map = _get_vlan_qos_map(
                context, name, inventory_hostname, "ingress")
            if ingress_qos_map is not None:
                iface["vlan"]["ingress-qos-map"] = ingress_qos_map

            egress_qos_map = _get_vlan_qos_map(
                context, name, inventory_hostname, "egress")
            if egress_qos_map is not None:
                iface["vlan"]["egress-qos-map"] = egress_qos_map

            # Ensure parent is initialized
            get_iface(parent)

        else:
            if "type" not in iface:
                # Check for explicit type configuration via <network>_type
                iface_type = networks.net_attr(
                    context, name, "type", inventory_hostname)
                iface["type"] = (
                    iface_type
                    if iface_type else _default_iface_type(iface_name))

            # Process structured ethtool configuration for advanced tuning
            ethtool_config = networks.net_attr(
                context, name, "ethtool_config", inventory_hostname)
            if ethtool_config:
                try:
                    processed_config = _process_ethtool_config(ethtool_config)
                    if processed_config:
                        iface["ethtool"] = processed_config
                except ValueError as e:
                    raise ValueError(
                        f"Invalid ethtool configuration for network "
                        f"'{name}': {e}")

    # Configure virtual Ethernet patch links to connect Linux bridges that
    # carry provision/cleaning/external networks into OVS.
    for veth in networks.get_ovs_veths(context, names, inventory_hostname):
        bridge_name = veth["bridge"]
        phy_name = veth["name"]
        peer_name = veth["peer"]

        bridge_iface = get_iface(bridge_name)
        bridge_iface["type"] = "linux-bridge"
        bridge_config = bridge_iface.get("bridge")
        if not isinstance(bridge_config, dict):
            bridge_config = {}
            bridge_iface["bridge"] = bridge_config

        bridge_ports = bridge_config.get("port")
        if not isinstance(bridge_ports, list):
            bridge_ports = []
            bridge_config["port"] = bridge_ports

        normalized_bridge_ports = []
        for port in bridge_ports:
            port_name = _port_name(port)
            if port_name:
                normalized_bridge_ports.append({"name": str(port_name)})

        bridge_config["port"] = normalized_bridge_ports
        bridge_ports = normalized_bridge_ports

        if not any(_port_name(port) == phy_name for port in bridge_ports):
            bridge_ports.append({"name": phy_name})

        phy_iface = get_iface(phy_name)
        phy_iface["type"] = "veth"
        phy_iface["veth"] = {"peer": peer_name}
        if veth.get("mtu"):
            phy_iface["mtu"] = veth["mtu"]
        _disable_ip_config(phy_iface)

        peer_iface = get_iface(peer_name)
        peer_iface["type"] = "veth"
        peer_iface["veth"] = {"peer": phy_name}
        if veth.get("mtu"):
            peer_iface["mtu"] = veth["mtu"]
        _disable_ip_config(peer_iface)

    # Filter routes that have next-hop information
    valid_routes = []
    for route in routes:
        if not isinstance(route, dict):
            continue
        has_next_hop_address = route.get("next-hop-address") is not None
        has_next_hop_interface = route.get("next-hop-interface") is not None
        has_next_hop = has_next_hop_address or has_next_hop_interface
        if has_next_hop:
            valid_routes.append(route)

    # Sort interfaces to ensure dependencies come before dependents.
    # Bridges must come after their ports, VLANs after their base interfaces.
    def interface_sort_key(iface):
        iface_type = iface.get("type", "ethernet")
        # Process in order: ethernet, bond, veth, vlan, then bridges
        # This ensures ports exist before bridges that use them
        type_order = {
            "dummy": 0,      # Dummy interfaces are base types like ethernet
            "ethernet": 0,
            "bond": 1,
            "veth": 2,
            "vlan": 3,
            "linux-bridge": 4,
        }
        return type_order.get(iface_type, 5)

    sorted_interfaces = sorted(interfaces.values(), key=interface_sort_key)

    return {
        "interfaces": sorted_interfaces,
        "routes": {"config": valid_routes},
        "route-rules": {"config": rules}
    }


def get_filters():
    return {
        "nmstate_config": nmstate_config,
    }
