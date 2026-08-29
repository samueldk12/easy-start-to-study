output "project_metadata_file" {
  value       = local_file.environment_metadata.filename
  description = "Path to generated deployment metadata"
}
