FROM node:20-slim

# Create app directory
WORKDIR /usr/src/app

# Install app dependencies
COPY package*.json ./
RUN npm install --production

# Copy the rest of the code
COPY . .

# Inform Docker that the app listens on 5000
EXPOSE 80

# Start the application
CMD [ "node", "server.js" ]