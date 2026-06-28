-- Options are automatically loaded before lazy.nvim startup
-- Default options that are always set: https://github.com/LazyVim/LazyVim/blob/main/lua/lazyvim/config/options.lua
-- Add any additional options here
vim.g.colorscheme = "habamax"
vim.o.scrolloff = 999
-- vim.cmd([[colorscheme catppuccin]])

-- Позволяет перемещать курсор на пустые виртуальные строки в самом конце файла
vim.opt.virtualedit:append("onemore")
-- Самое главное: разрешаем скролл "в пустоту"
vim.cmd([[set display=lastline]])
