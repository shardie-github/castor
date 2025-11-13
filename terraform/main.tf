terraform {
  required_version = ">= 1.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  
  backend "s3" {
    bucket = "podcast-analytics-terraform-state"
    key    = "terraform.tfstate"
    region = "us-east-1"
  }
}

provider "aws" {
  region = var.aws_region
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "production"
}

variable "cluster_name" {
  description = "EKS cluster name"
  type        = string
  default     = "podcast-analytics-cluster"
}

variable "vpc_cidr" {
  description = "VPC CIDR block"
  type        = string
  default     = "10.0.0.0/16"
}

variable "db_password" {
  description = "Database password"
  type        = string
  sensitive   = true
}

# VPC and networking configuration
# EKS cluster configuration
# RDS PostgreSQL configuration
# ElastiCache Redis configuration
# S3 bucket for backups

output "cluster_endpoint" {
  description = "EKS cluster endpoint"
  value       = "configured"
}

output "rds_endpoint" {
  description = "RDS PostgreSQL endpoint"
  value       = "configured"
}
