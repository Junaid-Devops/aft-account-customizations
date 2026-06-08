resource "terraform_data" "netskope_provisioning" {
  # Forces this script to run exactly once when an account passes pipeline changes
  triggers_replace = [
    var.account_id
  ]

  provisioner "local-exec" {
    command = "python3 ${path.module}/netskope_customization.py"
  }
}