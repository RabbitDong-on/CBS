#!/bin/bash

mybrowser=""

firefox=$HOME/bin/firefox
chrome=$HOME/bin/chrome
safari=$HOME/bin/safari

file=/tmp/output.html

# -------------------------------------------- setup
function setupApps {

    browser=nothing
    pdf=nothing

    firefox=$HOME/bin/firefox
    chrome=$HOME/bin/chrome
    safari=$HOME/bin/safari

    skim=$HOME/bin/skim
    acroread=$HOME/bin/acroread

    if      [ -e $firefox ]; then browser=$firefox
    else if [ -e $chrome  ]; then browser=$chrome
    else if [ -e $safari  ]; then browser=$safari
    fi
    fi
    fi
    
    if      [ -e $skim     ]; then pdf=$skim
    else if [ -e $acroread ]; then pdf=$acroread
    fi
    fi
}


# -------------------------------------------- runAll
function runAll {
    setupApps
}


# ------
runAll $*

browser $file

exit
