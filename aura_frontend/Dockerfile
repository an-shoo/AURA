# Use a Node.js base image
FROM node:18-alpine

# Set the working directory
WORKDIR /app

# Copy package.json and package-lock.json (or yarn.lock)
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy the rest of the frontend application code
COPY . .

# Expose the Vite development server port
EXPOSE 5173

# Command to run the development server
CMD ["npm", "run", "dev", "--", "--host"]