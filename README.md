# Person Detection API

        This application provides an API endpoint for detecting persons in images using YOLO and RT-DETR models.

        ## Features

        - Detects persons in images using two different models (YOLO and RT-DETR)
        - Finds common detections between the models for higher accuracy
        - Returns bounding box coordinates for detected persons
        - Containerized with Docker for easy deployment

        ## Production Setup (Default)

        To run the application in production mode (default):

        ```bash
        docker-compose up --build
        ```

        This will start the application with Gunicorn, which is a production-ready WSGI server.

        ## Development Setup

        For development and testing, use the development configuration:

        ```bash
        docker-compose -f docker-compose.dev.yml up --build
        ```

        This will start the application with the Flask development server, which is suitable for development and testing purposes.

        ## API Usage

        ### Detect Persons

        **Endpoint:** `POST /detect_persons`

        **Request:**
        - Content-Type: multipart/form-data
        - Body: 
          - `image`: Image file (supported formats: jpg, jpeg, png, bmp, tiff, webp)

        **Response:**
        ```json
        {
          "has_person": true,
          "bounding_box": {
            "X": 100.5,
            "Y": 150.2,
            "WIDTH": 200.3,
            "HEIGHT": 300.1
          }
        }
        ```

        If no person is detected:
        ```json
        {
          "has_person": false,
          "bounding_box": null
        }
        ```

        ## Development vs Production Server

        When running the application, you might see this warning:

        ```
        WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.
        ```

        This warning appears when using Flask's built-in development server, which is not designed for production use. The warning is normal and can be safely ignored during development.

        For production deployments, this application uses Gunicorn, which is a production-ready WSGI server. You can control which server to use by setting the `SERVER_TYPE` environment variable:

        - `SERVER_TYPE=flask`: Uses Flask's development server
        - `SERVER_TYPE=gunicorn`: Uses Gunicorn (default for production)

        ## Configuration

        The application can be configured using environment variables:

        - `ENV`: Environment (development/production)
        - `FLASK_ENV`: Flask environment (development/production)
        - `SERVER_TYPE`: Server type (flask/gunicorn)

        These can be set in the docker-compose files or passed directly to the container.

        ## Resource Requirements

        This application uses two AI models for person detection, which can be resource-intensive:

        1. YOLO model (yolo11l.pt)
        2. RT-DETR model (loaded from HuggingFace)

        The production configuration allocates the following resources:
        - CPU: 2 cores (with 1 core reserved)
        - Memory: 4GB (with 2GB reserved)

        These resources should be sufficient for most use cases. However, if you're processing large images or handling multiple concurrent requests, you might need to adjust these limits based on your specific hardware and workload.

        For development and testing with smaller workloads, lower resource allocations may be sufficient.

        ## N8N Workflow Automation

        This project also includes [N8N](https://n8n.io/), a powerful workflow automation tool that can be used to create automated workflows with the Person Detection API and other services.

        ### Accessing N8N

        After starting the containers with `docker-compose up`, you can access the N8N interface at:

        ```
        http://localhost:5678
        ```

        ### Data Persistence

        N8N is configured with data persistence using Docker volumes. This ensures that your workflows, credentials, and other N8N data are preserved even if you remove and reinstall Docker.

        The persistent data is stored in a Docker volume named `n8n_data`, which is mounted to the `/home/node/.n8n` directory in the N8N container.

        ### N8N Configuration

        The N8N service is configured with the following environment variables:

        - `N8N_HOST`: The hostname for N8N (set to 'n8n')
        - `N8N_PORT`: The port N8N runs on (5678)
        - `N8N_PROTOCOL`: The protocol used (http)
        - `NODE_ENV`: Environment (production)
        - `WEBHOOK_URL`: URL for webhooks (http://localhost:5678/)
        - `GENERIC_TIMEZONE`: Timezone setting (Asia/Jerusalem)

        You can modify these settings in the docker-compose.yml file as needed.

-------------------------------------------------------------------------------------------

# N8N Security Configuration

          This document provides instructions on how to set up and use the secure N8N configuration with a non-standard port and HTTPS.

          ## Overview of Changes

          The following security enhancements have been implemented:

          1. **Non-standard Port**: Changed the default N8N port from 5678 to 8743 to avoid port scanning detection
          2. **HTTPS Support**: Configured N8N to use HTTPS instead of HTTP
          3. **SSL Certificates**: Added support for SSL certificates
          4. **Encryption Key**: Added a configurable encryption key for sensitive data

          ## Setup Instructions

          ### 1. Generate SSL Certificates

          #### Option 1: Self-signed Certificates (for Development/Testing)

          Run the provided script to generate self-signed certificates:

          ```bash
          cd n8n
          ./generate-ssl-certs.sh
          ```

          This will create:
          - `ssl/privkey.pem` (private key)
          - `ssl/fullchain.pem` (certificate)

          #### Option 2: Let's Encrypt Certificates (for Production)

          For production environments, use Let's Encrypt to obtain trusted certificates:

          1. Make sure you have a domain name pointing to your server
          2. Install certbot on your server
          3. Run the provided script:

          ```bash
          cd n8n
          ./setup-letsencrypt.sh your-domain.com
          ```

          This will:
          - Obtain certificates from Let's Encrypt
          - Copy them to the ssl directory
          - Provide instructions for certificate renewal

          ### 2. Start N8N

          Start N8N with the secure configuration:

          ```bash
          # For production
          docker-compose up -d

          # For development
          docker-compose -f docker-compose.dev.yml up -d
          ```

          ### 3. Access N8N

          Access N8N through your browser at:

          ```
          https://localhost:8743
          ```

          Or if using a domain:

          ```
          https://your-domain.com:8743
          ```

          ## Additional Security Recommendations

          1. **Firewall Configuration**: Configure your firewall to only allow access to port 8743 from trusted IP addresses
          2. **Reverse Proxy**: Consider using a reverse proxy like Nginx or Traefik for additional security layers
          3. **Regular Updates**: Keep N8N and all dependencies up to date
          4. **Access Control**: Implement proper authentication and authorization
          5. **Monitoring**: Set up monitoring and alerting for suspicious activities
          6. **Encryption Key**: The encryption key is automatically generated when the container starts. If you need to persist data between restarts, you should set a fixed encryption key in the docker-compose file.

          ## Troubleshooting

          ### Certificate Issues

          If you encounter certificate issues:

          1. Verify that the certificates are correctly generated and placed in the n8n/ssl directory
          2. Check the permissions of the certificate files
          3. Ensure the paths in the docker-compose files match the actual certificate locations

          ### Connection Issues

          If you can't connect to N8N:

          1. Verify that the container is running: `docker-compose ps`
          2. Check the logs for errors: `docker-compose logs n8n`
          3. Ensure the port is accessible and not blocked by a firewall  