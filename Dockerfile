# FROM python:3.12-slim-bookworm
FROM python:3.11-slim-trixie

# Аргументы для создания пользователя с правильными правами
ARG USER_ID
ARG GROUP_ID
ARG USERNAME

# Установка системных зависимостей
RUN apt-get update && apt-get install -y --no-install-recommends \
  zsh \
  build-essential \
  curl \
  git \
  # neovim \
  ffmpeg \
  ripgrep \
  fd-find \
  xz-utils \
  gcc \
  nodejs \
  npm \
  build-essential \
  # npm install -g tree-sitter-cli \
  && apt-get clean && rm -rf /var/lib/apt/lists/*

# Установка Poetry через pip
RUN pip install --no-cache-dir "poetry>=1.7.0" && \
  poetry config virtualenvs.create true && \
  poetry config virtualenvs.in-project true && \
  poetry config virtualenvs.options.always-copy true


# Настройка окружения
ENV PYTHONDONTWRITEBYTECODE=1 \
  PYTHONUNBUFFERED=1 \
  POETRY_VIRTUALENVS_CREATE=true \
  POETRY_VIRTUALENVS_IN_PROJECT=true

# Создание пользователя
RUN groupadd --gid ${GROUP_ID} ${USERNAME} && \
  useradd --uid ${USER_ID} --gid ${GROUP_ID} -m ${USERNAME} && \
  mkdir -p /home/${USERNAME}/.config/nvim && \
  # mkdir -p /home/${USERNAME}/.scripts && \
  mkdir -p /home/${USERNAME}/.cache/pypoetry && \
  mkdir -p /home/${USERNAME}/.cache/nvim && \
  mkdir -p /home/${USERNAME}/.local/share/nvim && \
  mkdir -p /home/${USERNAME}/.local/state/nvim && \
  chown -R ${USERNAME}:${USERNAME} /home/${USERNAME}


# Копирование конфигураций
COPY .docker/nvim /home/${USERNAME}/.config/nvim
# COPY .docker/scripts /home/${USERNAME}/.scripts

# Настройка bashrc: алиасы, пути
RUN echo 'export PATH="$HOME/.local/bin:$PATH"' >> /home/${USERNAME}/.bashrc && \
  echo 'alias ll="ls -la"' >> /home/${USERNAME}/.bashrc && \
  echo 'alias po="poetry"' >> /home/${USERNAME}/.bashrc

# -------------------------------------------------
# Oh My Zsh
# -------------------------------------------------
RUN git clone https://github.com/ohmyzsh/ohmyzsh.git /home/${USERNAME}/.oh-my-zsh && \
  curl -fsSL 'https://raw.githubusercontent.com/sanek200000/Linux_sources/refs/heads/main/.zshrc' -o /home/${USERNAME}/.zshrc && \
  curl -fsSL 'https://raw.githubusercontent.com/sanek200000/Linux_sources/refs/heads/main/heist_red.zsh-theme' -o /home/${USERNAME}/.oh-my-zsh/themes/heist.zsh-theme && \
  git clone https://github.com/zsh-users/zsh-syntax-highlighting.git /home/${USERNAME}/.oh-my-zsh/plugins/zsh-syntax-highlighting && \
  git clone https://github.com/zsh-users/zsh-autosuggestions.git /home/${USERNAME}/.oh-my-zsh/plugins/zsh-autosuggestions && \
  chown -R ${USERNAME}:${USERNAME} /home/${USERNAME}/.oh-my-zsh


# -------------------------------------------------
# install nvim 
# -------------------------------------------------
RUN curl -LO https://github.com/neovim/neovim/releases/latest/download/nvim-linux-x86_64.tar.gz \
  && tar -C /opt -xzf nvim-linux-x86_64.tar.gz \
  && ln -s /opt/nvim-linux-x86_64/bin/nvim /usr/local/bin/nvim \
  && rm nvim-linux-x86_64.tar.gz

RUN npm install -g tree-sitter-cli

# Отключаем создание venv и настраиваем генерацию прямо в систему
# ENV POETRY_VIRTUALENVS_CREATE=false
# Установка зависимостей без создания окружения
# RUN poetry install --no-interaction --no-ansi

# Рабочая директория
WORKDIR /workspace

# Переключение на пользователя
# RUN mkdir /db && chown dev:dev /db
RUN chown -R ${USERNAME}:${USERNAME} /home/${USERNAME}
USER ${USERNAME}

# Единая точка входа (zsh для интерактивной разработки)
CMD ["zsh"]
