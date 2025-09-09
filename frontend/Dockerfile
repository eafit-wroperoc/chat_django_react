# Frontend Dockerfile (React)
FROM node:18-alpine

WORKDIR /app

# Install dependencies
COPY package*.json /app/
RUN npm install --legacy-peer-deps

# Copy source
COPY . /app

EXPOSE 3000

# Start development server (hot reload)
CMD ["npm", "start"]
