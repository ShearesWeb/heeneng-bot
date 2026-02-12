locals {
  images_bucket_name = "${var.env}-app-s3bucket-${var.project_code}images"
}

resource "aws_s3_bucket" "images" {
  bucket = local.images_bucket_name
}

resource "aws_s3_bucket_versioning" "images" {
  bucket = aws_s3_bucket.images.id

  versioning_configuration {
    status = "Disabled"
  }
}

resource "aws_s3_bucket_public_access_block" "images" {
  bucket = aws_s3_bucket.images.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
