#!/bin/bash
#
# based on: https://github.com/KSid/windows-vagrant-ansible
#
# Uncomment if behind a proxy server.
# export {http,https,ftp}_proxy='http://username:password@proxy-host:80'

# Detect package management system.
YUM=$(which yum 2>/dev/null)
APT_GET=$(which apt-get 2>/dev/null)

# Install Ansible and its dependencies if it's not installed already.
if ! command -v ansible >/dev/null; then
  echo "Installing Ansible dependencies and Git."
  if [[ ! -z ${YUM} ]]; then
    yum install -y git python python-devel
  elif [[ ! -z ${APT_GET} ]]; then
    apt-get install -y git python python-dev
  else
    echo "Neither yum nor apt-get are available."
    exit 1;
  fi

  echo "Installing pip via easy_install."
  wget https://raw.githubusercontent.com/ActiveState/ez_setup/v0.9/ez_setup.py
  python ez_setup.py && rm -f ez_setup.py
  easy_install pip
  # Make sure setuptools are installed crrectly.
  pip install setuptools --no-use-wheel --upgrade

  echo "Installing required python modules."
  pip install paramiko pyyaml jinja2 markupsafe

  echo "Installing Ansible."
  pip install ansible
fi

# Run the playbook.
echo "Running Ansible."
cd /vagrant && git checkout .
cp -R /vagrant/ansible /tmp
find /tmp/ansible -type f -exec chmod 644 {} \;
ansible-playbook -i 'localhost,' "/tmp/ansible/vagrant.yml" --extra-vars "is_windows=true" --vault-password-file "/tmp/ansible/.vault_pass.txt" --connection=local
rm -rf /tmp/ansible
