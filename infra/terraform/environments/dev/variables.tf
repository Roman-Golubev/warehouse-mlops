variable "yc_token" {
  type      = string
  sensitive = true
}

variable "yc_cloud_id" {
  type = string
}

variable "yc_folder_id" {
  type = string
}

variable "zone" {
  type    = string
  default = "ru-central1-a"
}

variable "vm_name" {
  type    = string
  default = "warehouse-mlops-vm"
}

variable "platform_id" {
  type    = string
  default = "standard-v3"
}

variable "cores" {
  type    = number
  default = 2
}

variable "memory" {
  type    = number
  default = 4
}

variable "core_fraction" {
  type    = number
  default = 20
}

variable "disk_size" {
  type    = number
  default = 30
}

variable "ssh_public_key" {
  type = string
}
