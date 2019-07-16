Vagrant.configure(2) do |config|
  config.vm.box = "sagepe/stretch"
  config.vm.network "forwarded_port", guest: 8000, host: 8000
  config.vm.provider "virtualbox" do |v|
    v.customize ["setextradata", :id, "VBoxInternal2/SharedFoldersEnableSymlinksCreate/vagrant", "1"]
    v.name   = 'vagrant-pombola-' + ( ENV['COUNTRY_APP'] || "south_africa" )
    v.memory = 4096
    v.cpus   = 2
  end
  config.vm.provision "shell",
    env: { "ES_VERSION" => ENV['ES_VERSION'] || "0.90.13" },
    path: "bin/vagrant-base.bash"
  config.vm.provision "shell",
    env: {
      "DATADIR"     => ENV['DATADIR']     || "/home/vagrant",
      "COUNTRY_APP" => ENV['COUNTRY_APP'] || "south_africa"
    },
    path: "bin/vagrant-install.bash",
    privileged: false
end
