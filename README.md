# Beatthemarket

## Introduction

**Django (Backend) + React (Frontend) + Postgres (Database) + Futu api + Redis in Docker**

This is a tool that used to find out **best price of warrant** in hk stock market. It used postgres database to store historical data which come from Futu Api (subscription needed) and it used timescale-db to shorten the process time. Django help us to manage the data between backend and Futu Api and commnicate with our react frontend using websocket.

To **start the Docker** :whale: :
```
Docker-compose up
```

After the installation
Frontend will be located at ```127.0.0.1:3000``` and Backend will be located at ```127.0.0.1:8000```

Ta-Lib needs to be installed manually (Bugs appear in alpine version of python).

To **install the Ta-Lib in Docker**:
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

To **activate Futu Api**, use ```docker exec -it {CONTAINER ID} sh``` 
``` 
/var/FutuOpenD_5.6.1818_Ubuntu16.04/FutuOpenD
input_phone_verify_code -code=
``` 

To **initiate Django**:
```
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

Frontend was deleted accidentally, shown as below:

![image](/pic/frontend_1.jpeg)
![image](/pic/frontend_2.jpeg))


## Contributors

- Wun Chi Hang, Jason jacksonwun@gmail.com

## License & Copyright

Licensed under the [MIT License](LICENSE).