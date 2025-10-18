#!/usr/bin/env bash
set -euo pipefail

if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
else
  echo "Файл .env не найден!"
  exit 1
fi

if ! command -v aws &> /dev/null; then
  echo "AWS CLI не найден. Установи его (brew install awscli)"
  exit 1
fi

if [ ! -d "${S3_RAW_BUCKET}" ]; then
  echo "Папка ${S3_RAW_BUCKET} не найдена!"
  exit 1
fi

S3_URL="${S3_PROTOCOL}://${S3_EXTERNAL_HOST}:${S3_PORT}"

aws configure set aws_access_key_id "$S3_ACCESS_KEY" --profile local
aws configure set aws_secret_access_key "$S3_SECRET_KEY" --profile local
aws configure set region "${AWS_REGION:-us-east-1}" --profile local
aws configure set output json --profile local

echo "Проверяю доступность S3..."
for i in {1..20}; do
  if aws --endpoint-url "$S3_URL" --profile local s3 ls >/dev/null 2>&1; then
    echo "S3 доступен (${S3_URL})"
    break
  fi
  echo "Ожидание S3... (${i}/20)"
  sleep 3
done

IFS=',' read -ra BUCKETS <<< "$S3_BUCKETS"
for BUCKET in "${BUCKETS[@]}"; do
  if ! aws --endpoint-url "$S3_URL" --profile local s3 ls "s3://${BUCKET}" >/dev/null 2>&1; then
    echo "Создаю бакет: ${BUCKET}"
    aws --endpoint-url "$S3_URL" --profile local s3 mb "s3://${BUCKET}"
  else
    echo "Бакет ${BUCKET} уже существует."
  fi
done

echo "Загружаю файлы из ${S3_RAW_BUCKET}/ в бакет ${S3_RAW_BUCKET}..."
# Use --size-only to skip files that already exist with same size (idempotent)
aws --endpoint-url "$S3_URL" --profile local s3 sync ${S3_RAW_BUCKET}/ "s3://${S3_RAW_BUCKET}/" --size-only

echo "Загрузка завершена успешно!"
