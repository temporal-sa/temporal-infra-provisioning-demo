variable "endpoint" {
  type = string
  default = "saas-api.tmprl.cloud:443"
}

variable "allow_insecure" {
  type = bool
  default = false
}


variable "prefix" {
  type = string
  default = "temporal-sa"
}

