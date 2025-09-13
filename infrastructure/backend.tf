terraform {
  backend "s3" {
    bucket         = "hoopstat-haus-tfstate"
    key            = "hoopstat-haus/prod/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "hoopstat-haus-tflock"
  }
}