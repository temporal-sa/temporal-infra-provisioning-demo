variable "endpoint" {
  type = string
  default = "saas-api.tmprl.cloud:443"
}

variable "region" {
  type = string
  default = "aws-us-west-2"
}

variable "allow_insecure" {
  type = bool
  default = false
}


variable "prefix" {
  type = string
}

