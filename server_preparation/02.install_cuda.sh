#!/bin/bash

# Останавливать скрипт при любой ошибке
set -e

echo "=== 1. Проверка наличия драйверов NVIDIA ==="
if ! command -v nvidia-smi &> /dev/null; then
    echo "Ошибка: Драйверы NVIDIA не найдены в системе."
    echo "Установите официальные драйверы NVIDIA (например: apt install nvidia-driver-535) перед запуском этого скрипта."
    exit 1
fi
nvidia-smi --query-gpu=name,driver_version --format=csv

echo -e "\n=== 2. Удаление старых или битых ключей (если они были) ==="
rm -f /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
rm -f /etc/apt/sources.list.d/nvidia-container-toolkit.list

echo -e "\n=== 3. Скачивание официального GPG-ключа NVIDIA ==="
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg


echo -e "\n=== 4. Добавление официального репозитория NVIDIA ==="
curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
  sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
  sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

echo -e "\n=== 5. Обновление базы пакетов и установка пакета ==="
apt-get update
apt-get install -y nvidia-container-toolkit

echo -e "\n=== 6. Настройка интеграции Docker и NVIDIA Runtime ==="
nvidia-container-toolkit configure --runtime=docker

echo -e "\n=== 7. Перезапуск службы Docker ==="
systemctl restart docker

echo -e "\n=== 8. Финальный тест: проверка GPU внутри тестового Docker-контейнера ==="
if docker run --rm --gpus all nvidia/cuda:12.0.0-base-ubuntu22.04 nvidia-smi &> /dev/null; then
    echo -e "\n[ НАСТРОЙКА УСПЕШНО ЗАВЕРШЕНА ]"
    echo "Docker теперь видит вашу видеокарту. Можно запускать контейнер!"
else
    echo -e "\n[ ОШИБКА ]"
    echo "Тестовый контейнер не смог получить доступ к GPU. Проверьте логи Docker."
    exit 1
fi
