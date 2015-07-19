# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure(2) do |config|
  config.vm.network "forwarded_port", guest: 5000, host: 5000
  config.ssh.forward_agent = true

  config.vm.provider "virtualbox" do |vb, override|
    override.vm.box = "ubuntu/precise32"
    vb.gui = true
  end

  config.vm.provider "docker" do |d|
    d.build_dir = "./vagrant"
    d.has_ssh = true
  end

  # provisioning
  require 'rbconfig'
  is_windows = (RbConfig::CONFIG['host_os'] =~ /mswin|mingw|cygwin/)

  if is_windows
    config.vm.provision "shell" do |sh|
      sh.path = "ansible/windows.sh"
    end
  else
    config.vm.provision "ansible" do |ansible|
      ansible.playbook = "ansible/vagrant.yml"
      ansible.limit = "all"
      ansible.verbose = "v"
      ansible.vault_password_file = "ansible/.vault_pass.txt"
      ansible.host_key_checking = false
    end
  end

end
