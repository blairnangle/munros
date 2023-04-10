resource "aws_lambda_function" "munros" {
  image_uri     = "${aws_ecr_repository.munros.repository_url}:latest"
  function_name = "munros"
  role          = aws_iam_role.munros.arn
  package_type  = "Image"
  timeout       = 60
}

resource "aws_iam_role" "munros" {
  name               = "munros"
  assume_role_policy = file("./templates/lambda-assume-role.json")
}

resource "aws_iam_policy" "lambda_secrets_manager" {
  policy = templatefile("templates/secrets-manager.json",
    {
      munrosStravaClientSecretArn = aws_secretsmanager_secret.strava_client_secret.arn,
      munrosRefreshTokenArn       = aws_secretsmanager_secret.strava_refresh_token.arn
    }
  )
}

resource "aws_iam_role_policy_attachment" "lambda_secrets_manager" {
  role       = aws_iam_role.munros.name
  policy_arn = aws_iam_policy.lambda_secrets_manager.arn
}

resource "aws_iam_policy" "lambda_logging" {
  policy = file("templates/lambda-logging.json")
}

resource "aws_iam_role_policy_attachment" "munros_logging" {
  role       = aws_iam_role.munros.name
  policy_arn = aws_iam_policy.lambda_logging.arn
}
