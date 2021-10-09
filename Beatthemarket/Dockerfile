# Base Image
FROM python:3.9.6
ENV PYTHONUNBUFFERED=1
WORKDIR /code
COPY requirements.txt /code/
RUN pip install -r requirements.txt
RUN pip install --upgrade pip
RUN pip install djangorestframework
RUN pip install markdown
RUN pip install django-filter
RUN pip install tqdm
# COPY . /code/
RUN apt-get update && apt-get install sudo
ENV TZ Asia/Hong_Kong

# # create and set working directory
# RUN mkdir /app
# WORKDIR /app

# # Add current directory code to working directory
# ADD . /app/

# # set default environment variables
# ENV PYTHONUNBUFFERED 1
# ENV LANG C.UTF-8

# # set project environment variables
# # grab these via Python's os.environ
# # these are 100% optional here
# ENV PORT=8000

# # Install system dependencies
# RUN apt-get update && apt-get install -y --no-install-recommends \
#         tzdata \
#         python3-setuptools \
#         python3-pip \
#         python3-dev \
#         python3-venv \
#         git \
#         && \
#     apt-get clean && \
#     rm -rf /var/lib/apt/lists/*

# # install environment dependencies
# RUN pip3 install --upgrade pip 
# RUN pip3 install pipenv
# RUN pip install -r requirements.txt

# # Install project dependencies
# # RUN pipenv install --skip-lock --system --dev
# RUN pipenv install

# EXPOSE 8000
# # CMD gunicorn cfehome.wsgi:application --bind 0.0.0.0:$PORT

# Ta Lib
# WORKDIR /var
# RUN tar -xzf ta-lib-0.4.0-src.tar.gz
# RUN cd ta-lib/
# RUN ./configure --prefix=/usr
# RUN make
# RUN sudo make install
# pip install ta-lib