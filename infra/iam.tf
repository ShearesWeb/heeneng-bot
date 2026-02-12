locals {
  lambda_execution_role_name   = "${var.env}-mgmt-iamrole-${var.project_code}"
  lambda_execution_policy_name = "${var.env}-mgmt-iampolicy-${var.project_code}"
}

module "lambda_execution_role" {
  source = "./modules/iam_role"
  name   = local.lambda_execution_role_name
  policy_attachments = [
    "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
  ]
  custom_policy = {
    name        = local.lambda_execution_policy_name
    description = "Allow Lambda to read images from S3."
    statements = {
      ImagesBucketList = {
        effect = "Allow"
        actions = [
          "s3:ListBucket"
        ]
        resources = [
          aws_s3_bucket.images.arn
        ]
      }
      ImagesBucketRead = {
        effect = "Allow"
        actions = [
          "s3:GetObject",
          "s3:GetObjectVersion"
        ]
        resources = [
          "${aws_s3_bucket.images.arn}/*"
        ]
      }
    }
  }
}
