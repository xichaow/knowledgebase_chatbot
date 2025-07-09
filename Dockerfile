FROM python:3.11

# Create a non-root user
RUN useradd -m -u 1000 user

# Set user environment
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

# Set working directory
WORKDIR $HOME/app

# Copy files
COPY --chown=user . .

# Install dependencies
RUN pip install -r requirements.txt

# Expose the port 
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Command to run the application
CMD chainlit run app.py --port ${PORT:-8000} --host 0.0.0.0