resource "aws_ecr_repository" "munros" {
  name                 = "munros"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Name = "munros"
  }
}
