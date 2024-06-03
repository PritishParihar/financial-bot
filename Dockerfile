# Use the official Python image from the Docker Hub
FROM python:3.8

# Set environment variables
ENV PYTHONUNBUFFERED 1

# Create and set the working directory
RUN mkdir /workdir
WORKDIR /workdir

# Copy the requirements.txt file into the container
COPY requirements.txt /workdir/

# Upgrade pip and install the dependencies
RUN pip install --upgrade pip wheel
RUN pip install -r requirements.txt

# Copy the rest of the application code into the container
COPY . /workdir/

# Set the command to run the Flask application
CMD ["python", "-m", "flask", "run", "--host=0.0.0.0", "--port=9000"]