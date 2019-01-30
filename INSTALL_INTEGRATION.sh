#!/bin/bash

# enable error exiting
set -e

ROOT=`dirname $(readlink -e $0)`
CHATBOT=chatbot
SOURCE=$ROOT/$CHATBOT

# if you install FS from source, you should set INSTALL_FREESWITCH and
# INSTALL_CONF_DIR before run this script. In fact, INSTALL_FREESWITCH should
# be equal to INSTALL_CONF_DIR (em... maybe, ^_^. Your choice!)
#   e.g. export INSTALL_CONF_DIR=freeswitch-path
INSTALL_FREESWITCH=${INSTALL_FREESWITCH:-/usr/share/freeswitch}
# we will install our packages to scripts direcotry of FreeSWITCH, and make
# soft link for configure files (dialplan, grammar)
INSTALL_DIR=${INSTALL_DIR:-$INSTALL_FREESWITCH/scripts}
INSTALL_CONF_DIR=${INSTALL_CONF_DIR:-/etc/freeswitch}

DEVMODE=${DEVMODE:-true}

function _install() {
    # install packages
    if $DEVMODE; then
        ln -sv $SOURCE $INSTALL_DIR/$CHATBOT
    else
        cp -rv $SOURCE $INSTALL_DIR/$CHATBOT
    fi
    # make soft link for configure files of FreeSWITCH
    ln -sv $INSTALL_DIR/$CHATBOT/freeswitch/dialplan/chatbot.xml \
        $INSTALL_CONF_DIR/dialplan/default/chatbot.xml
    ln -sv $INSTALL_DIR/$CHATBOT/freeswitch/grammar/chatbot-empty.xml \
        $INSTALL_FREESWITCH/grammar/chatbot-empty.xml
}

function _uninstall() {
    rm -v $INSTALL_CONF_DIR/dialplan/default/chatbot.xml || true
    rm -v $INSTALL_FREESWITCH/grammar/chatbot-empty.xml || true
    if [ -L "$INSTALL_DIR/$CHATBOT" ]; then
        rm -v "$INSTALL_DIR/$CHATBOT" || true
    else
        rm -rv "$INSTALL_DIR/$CHATBOT" || true
    fi
}

# run command
case $1 in
    uninstall)
        _uninstall
        ;;
    *)
        _install
        ;;
esac
