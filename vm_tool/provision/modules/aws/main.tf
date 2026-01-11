terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.16"
    }
  }
  required_version = ">= 1.2.0"
}

provider "aws" {
  region = var.region
}

variable "region" {
  default = "us-west-2"
}

variable "instance_type" {
  default = "t2.micro"
}

resource "aws_instance" "app_server" {
  ami           = "ami-830c94e3"
  instance_type = var.instance_type

  tags = {
    Name = "VMToolInstance"
  }
}

output "instance_ip" {
  value = aws_instance.app_server.public_ip
}
