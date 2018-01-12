# Command line tools for the AcoustID.biz "priv" API

Install FFmpeg:

    sudo apt-get install ffmpeg

Install Chromaprint:

    cd /tmp
    wget https://github.com/acoustid/chromaprint/releases/download/v1.4.2/chromaprint-fpcalc-1.4.2-linux-$(uname -m).tar.gz
    tar xvf chromaprint-fpcalc-1.4.2-linux-$(uname -m).tar.gz
    sudo mv chromaprint-fpcalc-1.4.2-linux-$(uname -m)/fpcalc /usr/local/bin/fpcalc

Install:

    sudo pip install acoustid-priv-tools

Upload fingerprints for your music catalog:

    acoustid-priv-sync -d /path/to/music
