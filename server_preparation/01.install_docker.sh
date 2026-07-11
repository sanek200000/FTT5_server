#!/bin/bash

# Накапливать ошибки и завершать скрипт при сбое
set -e

echo "=== Обновление индексов пакетов ==="
sudo apt-get update

echo "=== Установка зависимостей ==="
sudo apt-get install -y ca-certificates curl gnupg lsb-release

echo "=== Добавление официального GPG-ключа Docker ==="
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://docker.com | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg --yes
sudo chmod a+r /etc/apt/keyrings/docker.gpg

echo "=== Настройка репозитория Docker ==="
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://docker.com \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

echo "=== Установка Docker Engine ==="
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

echo "=== Создание группы docker (если не существует) ==="
sudo groupadd -f docker

echo "=== Добавление текущего пользователя в группу docker ==="
sudo usermod -aG docker $USER

echo "=== Применение изменений группы без перезапуска сессии ==="
echo "Проверка работы Docker от имени пользователя $USER..."
sg docker -c "docker run --rm hello-world"

echo "=== Установка успешно завершена! ==="
echo "Чтобы изменения вступили в силу для всех новых терминалов, перезапустите сессию (вылогиньтесь и войдите снова) или выполните команду: newgrp docker"
