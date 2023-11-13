import subprocess
import os
import getopt, sys
import shutil
from pathlib import Path
from string import Template

# HOME_DIR = os.environ['HOME']
BIN_DIR = "/usr/local/bin"

def run(cmd):
    print(f"[Running] {cmd}")
    if os.environ.get('DEBUG') != '1':
        subprocess.run(cmd, shell=True, check=True)

# install oh-my-zsh
def install_oh_my_zsh():
    oh_my_zsh_dir = os.path.join(HOME_DIR, ".oh-my-zsh")
    if os.path.exists(oh_my_zsh_dir):
        print("found ~/.oh-my-zsh")
    else:
        response = input("install oh-my-zsh? [ynq] ")
        if response == 'y':
            print("installing oh-my-zsh")
            subprocess.run(["git", "clone", "https://github.com/robbyrussell/oh-my-zsh.git", oh_my_zsh_dir], check=True)
        elif response == 'q':
            exit()
        else:
            print("skipping oh-my-zsh, you will need to change ~/.zshrc")
    print("Copying custom themes")
    subprocess.run([f"cp -r themes/* {oh_my_zsh_dir}/themes"], shell=True, check=False)

# install homebrew
def install_homebrew():
    print("Installing Homebrew, the OSX package manager...If it's already installed, this will do nothing.")
    run('/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"')
    print("Installing Homebrew packages...There may be some warnings.")

# installing optional binaries
def install_bins():
    run('curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.5/install.sh | bash')
    run('brew install ack')
    run('brew install bat')

# install custom git commands to /usr/local/bin. This path is defined in PATH in .zshrc
def install_git_commands():
    print("Installing custom git commands")
    git_commands_source = os.path.join(os.getcwd(), "git-commands")
    git_commands_destination = BIN_DIR 
    for command in os.listdir(git_commands_source):
        if os.path.isfile(os.path.join(git_commands_source, command)):
            print(f"Copying {command} to {git_commands_destination}")
            subprocess.run(["cp", os.path.join(git_commands_source, command), git_commands_destination], check=True)


def link_file(file):
    home_file = Path(HOME_DIR) / f".{file.name}"
    print(f"linking {HOME_DIR}/{home_file.name}")
    try:
        home_file.symlink_to(Path(os.getcwd()) / file)
    except FileExistsError:
        home_file.unlink()  # Remove the existing file if exists.
        home_file.symlink_to(Path(os.getcwd()) / file)

def copy_files():
    objects = os.scandir()
    ignore = ["README.md", "LICENSE", "Rakefile", "install.py", ".gitmodules", ".git", ".DS_Store", "themes", ".gitignore", "git-commands"]
    for obj in objects:
        if obj.name in ignore:
            continue
        link_file(obj)


def main():
    # Remove 1st argument from the
    # list of command line arguments
    argumentList = sys.argv[1:]
    # Options
    options = "h:"
    # Long options
    long_options = ["help"]
    
    try:
        # Parsing argument
        arguments, values = getopt.getopt(argumentList, options, long_options)
        if len(arguments) == 0: 
            print ("Install from scratch")
            install_oh_my_zsh()
            install_homebrew()
            install_bins()
            install_git_commands()
            copy_files()
        else:
            for currentArgument, currentValue in arguments:
                if currentArgument in ("-h", "--help"):
                    print("Displaying help")

    except getopt.error as err:
        # output error, and return with an error code
        print (str(err))

if __name__ == "__main__":
    main()

