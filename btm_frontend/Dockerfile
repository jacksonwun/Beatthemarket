# pull official base image
FROM node:16-alpine

# set working directory
WORKDIR /var/app/btm_frontend

# install in global and ignore user as root
RUN npm install -g --unsafe-perm npm@latest
RUN npm install -g --unsafe-perm sass
RUN npm install -g --unsafe-perm npm-install-peers
RUN npm-install-peers

RUN npm install -g --unsafe-perm typescript
RUN npm install -g --unsafe-perm @craco/craco ts-loader --save-dev

RUN npm install typescript
RUN npx browserslist@latest --update-db
RUN npm install nodemon --save-dev
RUN npm i react-scripts-ts