# Use the official PostgreSQL image
FROM postgres:15

# Set environment variables for default credentials
ENV POSTGRES_USER=mytestuser \
    POSTGRES_PASSWORD=mypassword \
    POSTGRES_DB=mysuperdb

# Create a mount point for persistent data
VOLUME /var/lib/postgresql/data

# Expose PostgreSQL port
EXPOSE 5432

# Health check (for docker-compose)
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD pg_isready -U $POSTGRES_USER -d $POSTGRES_DB