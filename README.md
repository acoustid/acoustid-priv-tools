# Command line tools for the AcoustID.biz "priv" API

Install FFmpeg:

    sudo apt-get install ffmpeg

Install Chromaprint:

    cd /tmp
    wget https://github.com/acoustid/chromaprint/releases/download/v1.4.2/chromaprint-fpcalc-1.4.2-linux-$(uname -m).tar.gz
    tar xvf chromaprint-fpcalc-1.4.2-linux-$(uname -m).tar.gz
    sudo mv chromaprint-fpcalc-1.4.2-linux-$(uname -m)/fpcalc /usr/local/bin/fpcalc

Install:

    sudo virtualenv -p python2 /opt/acoustid-priv-tools
    sudo /opt/acoustid-priv-tools/bin/pip install https://github.com/acoustid/acoustid-priv-tools/archive/master.zip

Configure:

    $EDITOR ~/.config/acoustid-priv.conf

    [main]
    api-key=XXX
    catalog=mymusic

Upload fingerprints for your music catalog:

    acoustid-priv-sync -d /path/to/music

Monitor an online stream with hourly reports in CSV files:

    acoustid-priv-monitor -o 'acoustid-results-stream1-%Y-%m-%d-%H.csv' http://example.com/stream1.mp3
