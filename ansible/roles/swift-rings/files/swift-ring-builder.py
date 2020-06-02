#!/usr/bin/env python3

"""
Script to build a Swift ring from a declarative YAML configuration. This has
been built via a script to avoid repeated 'docker exec' commands which could
take a long time.

Usage:

python swift-ring-builder.py <config file path> <build path> <service name>

Example:

python swift-ring-builder.py /path/to/config.yml /path/to/builds object

Example configuration format:

---
part_power: 10
replication_count: 3
min_part_hours: 1
hosts:
  - host: swift1
    region: 1
    zone: 1
    ip: 10.0.0.1
    port: 6001
    replication_ip: 10.1.0.1
    replication_port: 6001
    devices:
      - device: /dev/sdb
        weight: 100
      - device: /dev/sdc
        weight: 100
"""
import subprocess
import sys

import yaml


class RingBuilder(object):
    """Helper class for building Swift rings."""

    def __init__(self, build_path, service_name):
        self.build_path = build_path
        self.service_name = service_name

    def get_base_command(self):
        return [
            'swift-ring-builder',
            '%s/%s.builder' % (self.build_path, self.service_name),
        ]

    def create(self, part_power, replication_count, min_part_hours):
        cmd = self.get_base_command()
        cmd += [
            'create',
            "{}".format(part_power),
            "{}".format(replication_count),
            "{}".format(min_part_hours),
        ]
        try:
            subprocess.check_call(cmd)
        except subprocess.CalledProcessError:
            print("Failed to create %s ring" % self.service_name)
            sys.exit(1)

    def add_device(self, host, device):
        cmd = self.get_base_command()
        cmd += [
            'add',
            '--region', "{}".format(host['region']),
            '--zone', "{}".format(host['zone']),
            '--ip', host['ip'],
            '--port', "{}".format(host['port']),
            '--replication-ip', host['replication_ip'],
            '--replication-port', "{}".format(host['replication_port']),
            '--device', device['device'],
            '--weight', "{}".format(device['weight']),
        ]
        try:
            subprocess.check_call(cmd)
        except subprocess.CalledProcessError:
            print("Failed to add device %s on host %s to %s ring" %
                  (host['host'], device['device'], self.service_name))
            sys.exit(1)

    def rebalance(self):
        cmd = self.get_base_command()
        cmd += [
            'rebalance',
        ]
        try:
            subprocess.check_call(cmd)
        except subprocess.CalledProcessError:
            print("Failed to rebalance %s ring" % self.service_name)
            sys.exit(1)


def build_rings(config, build_path, service_name):
    builder = RingBuilder(build_path, service_name)
    builder.create(config['part_power'], config['replication_count'],
                   config['min_part_hours'])
    for host in config['hosts']:
        devices = host['devices']
        # If no devices are present for this host, this will be None.
        if devices is None:
            continue
        for device in devices:
            builder.add_device(host, device)
    builder.rebalance()


def main():
    if len(sys.argv) != 4:
        raise Exception("Usage: {0} <config file path> <build path> "
                        "<service name>")
    config_path = sys.argv[1]
    build_path = sys.argv[2]
    service_name = sys.argv[3]
    with open(config_path) as f:
        config = yaml.load(f)
    build_rings(config, build_path, service_name)


if __name__ == "__main__":
    main()
