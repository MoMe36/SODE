#!/bin/bash 


lib_path=$(dirname $(realpath $0))
# echo $lib_path

# REMOVING EXISTING ENVS
if conda env list | grep -q sode_env; then 
    conda env remove -n sode_env
fi 

# CREATING NEW ENV AND INSTALLING PACKAGES
conda create -n sode_env -y python=3.10 numpy pandas
cd $lib_path
source "$HOME/anaconda3/bin/activate" "sode_env"
pip install -e . 

# COLLECTING OBSIDIAN FOR GRAPH VIZ
wget https://github.com/obsidianmd/obsidian-releases/releases/download/v1.6.7/Obsidian-1.6.7.AppImage -O $lib_path/Obsidian-1.6.7.AppImage
chmod +x $lib_path/Obsidian-1.6.7.AppImage

# FINAL STEPS (API KEY, CLI PREP, TEST RUN)
read -p "Provide your Gemini API key (will be saved in default path $HOME/.gemini.txt)>>>" api_key
echo $api_key > $HOME/.gemini.txt

# CREATING THE BIN DIRECTORY IF MISSING 
if [ ! -d $HOME/.local/bin ]; then
    mkdir -p $HOME/.local/bin
fi

# COPYING THE CLI SCRIPT
cp $lib_path/sode_cli.sh $HOME/.local/bin/sode_cli.sh
chmod +x $HOME/.local/bin/sode_cli.sh


# ADDING THE BIN DIRECTORY TO PATH TO ENSURE CLI IS ACCESSIBLE
export_line="export PATH=\$PATH:$HOME/.local/bin"
if ! grep -q "$export_line" $HOME/.bashrc; then
    echo $export_line >> $HOME/.bashrc
fi
source $HOME/.bashrc

sode_cli.sh reset # to create the config file

# python $lib_path/sode_main.py # test_run 
echo "Installation complete >>> run sode_cli.sh to start"

