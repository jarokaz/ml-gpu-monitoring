locals {
    image_project       = "deeplearning-platform-release"
    post_startup_script_url = "https://raw.githubusercontent.com/jarokaz/community/master/tutorials/ml-gpu-monitoring/env-setup/install-dcgm.sh"
}

data "google_compute_network" "vm_network" {
  name = var.network_name
}

data "google_compute_subnetwork" "vm_subnetwork" {
  name   = var.subnet_name
  region = var.region
}

resource "google_notebooks_instance" "notebook_instance" {
    name             = "${var.name_prefix}-vm"
    machine_type     = var.machine_type
    location         = var.zone

    network = data.google_compute_network.vm_network.id
    subnet  = data.google_compute_subnetwork.vm_subnetwork.id

    vm_image {
        project      = local.image_project
        image_family = var.image_family
    }

    install_gpu_driver  = true
    post_startup_script = local.post_startup_script_url

    boot_disk_size_gb   = var.boot_disk_size
}
