#!/usr/bin/with-contenv bashio

export PRINTER_IP=$(bashio::config 'printer_ip')
python3 /server.py