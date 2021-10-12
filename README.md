# Beatthemarket

**Django backend + react frontend + psql + futu api + Docker + redis**

This is a tool that used to find out best price of warrant in hk stock market. It used postgres database to store historical data which come from Futu Api (subscription needed) and it used timescale-db to shorten the process time. Django help us to manage the data between backend and Futu Api and commnicate with our react frontend using websocket.

How to use:
```
Docker-compose up
```

After the installation
Frontend will be located at ```127.0.0.1:3000``` and Backend will be located at ```127.0.0.1:8000```

Ta-Lib needs to be installed manually (Bugs appear in alpine version of python).

Follow:
```
cd /var
tar -xzf ta-lib-0.4.0-src.tar.gz
cd ta-lib/
./configure --prefix=/usr
make
make install
pip install ta-lib
```

Clock skew Bug may occur when using window, use ```wsl --shutdown``` to restart VM.