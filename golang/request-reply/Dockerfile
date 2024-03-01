# Step 1: Use the official Golang image as the base image
FROM golang:1.22 as builder

# Step 2: Set the working directory inside the container
WORKDIR /app

# Copy the Go Modules manifests and download the dependencies
# This is done separately to leverage Docker cache
COPY go.mod go.sum ./
RUN go mod download

# Copy the rest of the source code
COPY . .

# Step 3: Build the Go app as a static binary
RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o hasher .

# Start a new stage from scratch for a lightweight final image
FROM alpine:latest  

WORKDIR /root/

# Copy the binary from the builder stage
COPY --from=builder /app/hasher .

# Step 4: Run the hasher binary when the container starts
CMD ["./hasher"]
