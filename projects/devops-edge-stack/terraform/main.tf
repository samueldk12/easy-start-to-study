terraform {
  required_version = ">= 1.5.0"
  required_providers {
    local = {
      source  = "hashicorp/local"
      version = "~> 2.4"
    }
  }
}

provider "local" {}

resource "local_file" "environment_metadata" {
  filename = "${path.module}/deployment-metadata.json"
  content = jsonencode({
    project_name = "devops-edge-stack"
    environment  = var.environment
    created_by   = "StackStudio"
  })
}
