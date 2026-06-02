data "yandex_vpc_network" "default" {
  name = "default"
}

data "yandex_vpc_subnet" "default_a" {
  name = "default-ru-central1-a"
}

resource "yandex_compute_instance" "vm" {
  name        = var.vm_name
  platform_id = var.platform_id
  zone        = var.zone

  resources {
    cores         = var.cores
    memory        = var.memory
    core_fraction = var.core_fraction
  }

  boot_disk {
    initialize_params {
      image_id = "fd8kdq6d0p8sij7h5qe3"
      size     = var.disk_size
      type     = "network-hdd"
    }
  }

  network_interface {
    subnet_id = data.yandex_vpc_subnet.default_a.id
    nat       = true
  }

  metadata = {
    ssh-keys = "ubuntu:${var.ssh_public_key}"
  }

  scheduling_policy {
    preemptible = true
  }
}
