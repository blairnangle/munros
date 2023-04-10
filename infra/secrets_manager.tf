resource "aws_secretsmanager_secret" "strava_client_secret" {
  name = "strava-client-secret"
}

resource "aws_secretsmanager_secret_version" "strava_client_secret" {
  secret_id     = aws_secretsmanager_secret.strava_client_secret.id
  secret_string = var.strava_client_secret
}

resource "aws_secretsmanager_secret" "strava_refresh_token" {
  name = "strava-refresh-token"
}
