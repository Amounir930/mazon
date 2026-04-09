# Simple Nginx container to serve the pre-built React app
FROM nginx:stable-alpine

# Copy the pre-built assets from the host
COPY dist /usr/share/nginx/html

# Copy custom Nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port
EXPOSE 80

# Start Nginx
CMD ["nginx", "-g", "daemon off;"]
