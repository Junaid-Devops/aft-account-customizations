resource "aws_budgets_budget" "total_cost" {
  name              = "budget-total-monthly"
  budget_type       = "COST"
  limit_amount      = "100"
  limit_unit        = "USD"
  time_period_end   = "2087-06-15_00:00"
  time_period_start = "2022-02-01_00:00"
  time_unit         = "MONTHLY"
}

resource "terraform_data" "netskope_provisioning" {
  # Forces this script to run exactly once when an account passes pipeline changes
  triggers_replace = [
    var.account_id
  ]

  provisioner "local-exec" {
    command = "python3 ${path.module}/netskope_customization.py"
  }
}