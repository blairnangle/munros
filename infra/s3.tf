resource "aws_s3_bucket" "munros" {
  bucket = "munros.blairnangle.com"
}

resource "aws_s3_bucket_public_access_block" "munros" {
  bucket = aws_s3_bucket.munros.id

  block_public_acls       = false
  block_public_policy     = false
  ignore_public_acls      = false
  restrict_public_buckets = false
}

resource "aws_s3_bucket_policy" "munros" {
  bucket = aws_s3_bucket.munros.id
  policy = templatefile("${path.module}/templates/s3.json", {
    awsAccountNumber = var.aws_account_number,
    lambdaRoleArn    = aws_iam_role.munros.arn,
    bucketName       = aws_s3_bucket.munros.bucket
  })
}

resource "aws_s3_bucket_cors_configuration" "munros" {
  bucket = aws_s3_bucket.munros.id

  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = ["GET"]
    allowed_origins = ["*"]
    expose_headers  = ["ETag"]
    max_age_seconds = 3000
  }
}
