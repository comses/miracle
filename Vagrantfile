# -*- mode: ruby -*-
# vi: set ft=ruby :

# All Vagrant configuration is done below. The "2" in Vagrant.configure
# configures the configuration version (we support older styles for
# backwards compatibility). Please don't change it unless you know what
# you're doing.
Vagrant.configure(2) do |config|
  # create mgmt node
  config.vm.define :dev do |dev_config|
	dev_config.vm.box = "ubuntu/trusty64"
	dev_config.vm.hostname = "dev"
	dev_config.vm.provider "virtualbox" do |vb|
		vb.memory = "1024"
	end	
	dev_config.vm.network :forwarded_port, guest: 8000, host: 8000  # Django
	dev_config.vm.network :forwarded_port, guest: 7400, host: 7400  # DeployR
	dev_config.vm.network :forwarded_port, guest: 3838, host: 3838  # Radiant
	dev_config.vm.network :forwarded_port, guest: 5432, host: 15432 # PostgreSQL

	dev_config.vm.provision :shell, path: "bootstrap-dev.sh"
  end
end
