genesis
=======

## vagrant for development
1. `git clone https://github.com/ecclesianuernberg/genesis`
2. `cd genesis`
3. `vim ansible/.vault_pass.txt` and add the vault password
4. place sql-dump in `ansible/roles/churchtools/files/`
5. `vagrant up`
6. `vagrant ssh`
7. `cd /vagrant`
8. `python manage.py runserver`
9. open browser and go to `http://localhost:5000`

## deploy
1. `ansible-playbook -i ansible/ecclesia ansible/deploy.yml -k --ask-vault-pass`
