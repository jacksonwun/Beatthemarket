# pull official base image
FROM node:12-alpine

# set working directory
WORKDIR /var/app/btm_frontend
COPY . ./

RUN npm install 
RUN npm install -g sass
RUN npm install -g npm-install-peers
RUN npm-install-peers