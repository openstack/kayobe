# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure('2') do |config|
  config.vm.hostname = 'controller1'

  config.vm.network 'private_network', ip: '192.168.33.3', auto_config: false

  config.vm.box = 'centos/stream8'

  # The default CentOS box comes with a root disk that is too small to fit a
  # deployment on so we need to make it bigger.
  config.disksize.size = '20GB'

  config.vm.provider 'virtualbox' do |vb|
    vb.memory = '4096'
    vb.linked_clone = true
  end

  config.vm.provider 'vmware_fusion' do |vmware|
    vmware.vmx['memsize'] = '4096'
    vmware.vmx['vhv.enable'] = 'TRUE'
    vmware.linked_clone = true
  end

  config.vm.provision 'shell', inline: <<-SHELL

    # Extend the root disk
    sudo parted "/dev/sda" ---pretend-input-tty <<EOF
resizepart
1
100%
Yes
-0
quit
EOF
    sudo xfs_growfs -d /

    echo "cat > /etc/selinux/config << EOF
SELINUX=disabled
SELINUXTYPE=targeted
EOF" | sudo -s
      cat /etc/selinux/config
  SHELL

  # NOTE: Reboot to apply selinux change, requires the reload plugin:
  #   vagrant plugin install vagrant-reload
  config.vm.provision :reload

  config.vm.provision 'shell', privileged: false, inline: <<-SHELL
    cat << EOF | sudo tee /etc/sysconfig/network-scripts/ifcfg-eth1
DEVICE=eth1
USERCTL=no
BOOTPROTO=none
IPADDR=192.168.33.3
NETMASK=255.255.255.0
ONBOOT=yes
EOF
    sudo ifup eth1

    /vagrant/dev/install-dev.sh

    # Configure the legacy development environment. This has been retained
    # while transitioning to the new development environment.
    cat > /vagrant/kayobe-env << EOF
export KAYOBE_CONFIG_PATH=/vagrant/etc/kayobe
export KOLLA_CONFIG_PATH=/vagrant/etc/kolla
EOF
    cp /vagrant/dev/dev-vagrant.yml /vagrant/etc/kayobe/
    cp /vagrant/dev/dev-hosts /vagrant/etc/kayobe/inventory
    cp /vagrant/dev/dev-vagrant-network-allocation.yml /vagrant/etc/kayobe/network-allocation.yml
  SHELL
end
