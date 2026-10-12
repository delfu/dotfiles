-- ============================================================
-- Neovim config (migrated from ~/.vimrc)
-- Plugin manager: lazy.nvim
-- ============================================================

-- ------------------------------------------------------------
-- Bootstrap lazy.nvim (auto-installs on first launch)
-- ------------------------------------------------------------
local lazypath = vim.fn.stdpath("data") .. "/lazy/lazy.nvim"
if not (vim.uv or vim.loop).fs_stat(lazypath) then
  vim.fn.system({
    "git", "clone", "--filter=blob:none",
    "https://github.com/folke/lazy.nvim.git",
    "--branch=stable",
    lazypath,
  })
end
vim.opt.rtp:prepend(lazypath)

-- ------------------------------------------------------------
-- Plugins
-- ------------------------------------------------------------
require("lazy").setup({
  -- Surround text objects (provides ys/cs/ds, e.g. ysiw')
  { "tpope/vim-surround" },

  -- Code/tag outline sidebar (needs `ctags` installed: brew install universal-ctags)
  { "preservim/tagbar" },

  -- Monokai colorscheme (Lua port, provides `colorscheme monokai`)
  {
    "tanvirtin/monokai.nvim",
    priority = 1000, -- load colorscheme before other plugins
    config = function()
      vim.cmd.colorscheme("monokai")
    end,
  },
  -- Markdown render
  {
	  'MeanderingProgrammer/render-markdown.nvim',
	  dependencies = { 'nvim-treesitter/nvim-treesitter', 'nvim-mini/mini.icons' },           -- standalone mini.icons (lighter than full mini.nvim)
	  -- dependencies = { 'nvim-treesitter/nvim-treesitter', 'nvim-tree/nvim-web-devicons' }, -- if you prefer nvim-web-devicons
	  ---@module 'render-markdown'
	  ---@type render.md.UserConfig
	  opts = {},
  },

  -- Solarized (was commented out in your .vimrc; uncomment to use)
  -- {
  --   "maxmx03/solarized.nvim",
  --   priority = 1000,
  --   config = function()
  --     vim.cmd.colorscheme("solarized")
  --   end,
  -- },
})

-- ------------------------------------------------------------
-- Visual / environment settings
-- ------------------------------------------------------------
vim.cmd("syntax enable")
vim.opt.ruler = true
vim.opt.number = true
vim.opt.relativenumber = true
vim.opt.showmode = true
vim.opt.background = "dark"

-- Popup-menu highlight colors
vim.api.nvim_set_hl(0, "Pmenu",    { bold = true, ctermfg = "white", ctermbg = "black", reverse = true })
vim.api.nvim_set_hl(0, "PmenuSel", { bold = true, ctermfg = "red",   ctermbg = "black", reverse = true })

-- ------------------------------------------------------------
-- Navigation / editing behavior
-- ------------------------------------------------------------
vim.opt.scrolloff = 10
vim.opt.backspace = { "indent", "eol", "start" }

-- ------------------------------------------------------------
-- Indentation
-- ------------------------------------------------------------
vim.opt.cindent = true
vim.opt.autoindent = true
vim.opt.tabstop = 4
vim.opt.shiftwidth = 4
vim.opt.cinkeys = "0{,0},:,0#,!^F"

-- ------------------------------------------------------------
-- Bell off
-- ------------------------------------------------------------
-- (t_vb from the old .vimrc is gone in Neovim; errorbells + visualbell cover it)
vim.opt.errorbells = false
vim.opt.visualbell = true

-- ============================================================
-- Keymaps
-- ============================================================

-- Disable J (join) / K (keyword lookup) -> just move down/up
vim.keymap.set("", "<S-j>", "j", { noremap = true })
vim.keymap.set("", "<S-k>", "k", { noremap = true })

-- ; as : for quick command entry
vim.keymap.set("", ";", ":", { noremap = true })

-- Insert/command-line mode shortcuts (original used `map!`)
local ic = { "i", "c" }
vim.keymap.set(ic, "<C-l>", "<ESC>Li",   { remap = true }) -- jump to last line on screen, insert
vim.keymap.set(ic, "<C-e>", "<ESC>$a",   { remap = true }) -- end of line
vim.keymap.set(ic, "<C-a>", "<ESC>^i",   { remap = true }) -- start of line
vim.keymap.set(ic, "<C-s>", "<ESC>:wq",  { remap = true }) -- write & quit
vim.keymap.set(ic, "<C-k>", "<ESC>lDi",  { remap = true }) -- delete after cursor
vim.keymap.set(ic, "<C-]>", "<ESC>>>i",  { remap = true }) -- indent right

-- Toggle paste mode and report state
vim.keymap.set("n", "<C-p>", ":set invpaste paste?<CR>", { noremap = true })

-- Surround word in single quotes (needs remap so vim-surround's `ys` resolves)
vim.keymap.set("n", "q'", "ysiw'", { remap = true })

-- Tagbar toggle
vim.keymap.set("i", "<F8>", "<ESC>:TagbarToggle<CR>", { noremap = true })
vim.keymap.set("n", "<F8>", ":TagbarToggle<CR>",      { noremap = true })

-- ============================================================
-- Autocommands
-- ============================================================

-- Strip auto-commenting/auto-wrap format options for every filetype
vim.api.nvim_create_autocmd("FileType", {
  pattern = "*",
  callback = function()
    vim.opt_local.formatoptions:remove({ "c", "r", "o" })
  end,
})
