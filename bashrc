
PATH=$PATH:$HOME/.rvm/bin # Add RVM to PATH for scripting

export ANDROID_NDK_ROOT=~/dev/android-ndk-r10e/

function fixxcode () {
	rm -rf ~/Library/Caches/com.apple.dt.Xcode/
	rm -rf ~/Library/Developer/Xcode/DerivedData/*
}

#launch zsh
if [ -t 1 ]; then
	exec zsh
fi
