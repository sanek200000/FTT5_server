return {
  "stevearc/conform.nvim",
  opts = {
    -- Включение форматирования при сохранении
    format_on_save = {
      timeout_ms = 3000,
      async = false,
      quiet = false,
    },
    -- Назначение форматировщика для конкретных языков
    formatters_by_ft = {
      python = { "black" }, -- Назначаем black главным для python
    },
    -- Дополнительные настройки для самого black (например, длина строки)
    formatters = {
      black = {
        prepend_args = { "--line-length", "120" }, -- 88 — стандарт для Black, можно поменять на 120
      },
    },
  },
}
