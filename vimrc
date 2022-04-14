""""""""""""""""""""""""""
" Turn off folding
"""""""""""""""""""""""""
noremap <S-j> j
noremap <S-k> k

"""""""""""""""""""""""""""""""""""""""""""""
" Environment + Visual Settings
"
"""""""""""""""""""""""""""""""""""""""""""""
syntax enable
set ruler
set number

" Set the highlighting on the Pmenu
highlight PMenu 		term=reverse cterm=bold ctermfg=white ctermbg=black
highlight PMenuSel 		term=reverse cterm=bold ctermfg=red ctermbg=black

"""""""""""""""""""""""""""""""""""""""""
" Basic Navigation and Text Manipulation
"
"""""""""""""""""""""""""""""""""""""""""

" Set the scroll offset to be 10 lines
set scrolloff=10
set backspace=indent,eol,start
" Map CTRL-L to go to the last line on the screen
map! <C-L> <ESC>Li

" Map CTRL-E to go to end of line
map! <C-e> <ESC>$a

" Map CTRL-A to go the start of line
map! <C-a> <ESC>^i

" Map CTRL-S to Write command
map! <C-s> <ESC>:wq

" Map CTRL-K to delete after the cursor
map! <C-k> <ESC>lDi

" Map CTRL-P to the go to toggle pastemode
" psych

" Map CTRL-] to tab right
map! <C-]> <ESC>>>i

map ; :

""""""""""""""""""""""""
" Global Indentation Rules 
"
""""""""""""""""""""""""
set cindent
set autoindent
set tabstop=4
set shiftwidth=4
set cinkeys=0{,0},:,0#,!^F


"""""""""""""""""
" Paste Toggle
"""""""""""""""""
nnoremap <C-p> :set invpaste paste?<CR>
set pastetoggle=<C-p>
set showmode

"""""""""""""""""""""""""""
"" Surround plugings
""""""""""""""""""""""""""

noremap q' ysiw'

"nnoremap q\" ysiw\"
"nnoremap q] ysiw]
"nnoremap q) ysiw)

""""""""""""""""""""""
" Solarized 
"""""""""""""""""""""
set background=dark
let g:solarized_termcolors=256
"colorscheme solarized
colorscheme monokai

"""""""""""""""""""""""
" Tagbars
""""""""""""""""""""""
imap <F8> <ESC>:TagbarToggle<CR>
nmap <F8> :TagbarToggle<CR>


""""""""""""""""""""""""""
" Turn off bell
"""""""""""""""""""""""""
set noerrorbells visualbell t_vb=
autocmd GUIEnter * set visualbell t_vb=

autocmd FileType * setlocal formatoptions-=c formatoptions-=r formatoptions-=o
