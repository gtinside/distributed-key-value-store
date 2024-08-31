provider "aws" {
  region = "us-east-1"  # Adjust the region as needed
}

# Define a security group to allow HTTP, HTTPS, and SSH
resource "aws_security_group" "web_sg" {
  name        = "web_sg"
  description = "Allow HTTP, HTTPS, and SSH access"

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  vpc_id = aws_vpc.main.id
}

# Define a VPC
resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/16"
}

# Define a subnet with public IP auto-assignment enabled
resource "aws_subnet" "my_subnet" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.1.0/24"
  availability_zone = "us-east-1a"  # Adjust as needed
  map_public_ip_on_launch = true  # Enable automatic public IP assignment
}

# Create an internet gateway and attach it to the VPC
resource "aws_internet_gateway" "igw" {
  vpc_id = aws_vpc.main.id
}

# Create a route table and a default route to the internet gateway
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.igw.id
  }
}

resource "aws_route_table_association" "public" {
  subnet_id      = aws_subnet.my_subnet.id
  route_table_id = aws_route_table.public.id
}

# Define the EC2 instances
resource "aws_instance" "core_cache" {
  count             = 3
  ami               = "ami-066784287e358dad1"  # Amazon Linux 2 AMI (Adjust the AMI ID as needed)
  instance_type     = "t2.micro"
  key_name          = "CoreCacheKey"  # Replace with your key pair name
  vpc_security_group_ids = [aws_security_group.web_sg.id]
  subnet_id         = aws_subnet.my_subnet.id  # Replace with your subnet ID
  associate_public_ip_address = true  # Ensure a public IP is assigned

  # User data script to install Python and Docker
  user_data = <<-EOF
              #!/bin/bash
              sudo yum update -y
              sudo yum install -y python3.11
              sudo python3 -m ensurepip --upgrade
              sudo yum install -y docker
              sudo service docker start
              sudo systemctl enable docker
              EOF

  tags = {
    Name = "core-cache-${count.index + 1}"
  }
}
