resource "terraform_data" "netskope_provisioning" {
  triggers_replace = [
    # Computes an MD5 checksum of the files. If you change a single character, 
    # the hash shifts, and Terraform will instantly re-execute the script.
    md5(file("${path.module}/netskope_customization.py")),
    md5(file("${path.module}/instances.json"))
  ]

  provisioner "local-exec" {
    command = "python3 ${path.module}/netskope_customization.py"
  }
}