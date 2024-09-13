provider "aws" {
  region = "us-east-1"  
}

terraform {
  backend "s3" {
    bucket         = "corecache-tf-state"
    key            = "tf-state/terraform.tfstate"
    region         = "us-east-1"
  }
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

  ingress {
    from_port   = 0
    to_port     = 0
    protocol    = "tcp"
    cidr_blocks = [aws_vpc.main.cidr_block]
    description = "Allow all internal traffic"
  }

  ingress {
    from_port   = 8000
    to_port     = 9000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow access to CoreCahce Service from outside"
  }

  ingress {
    from_port   = 2181
    to_port     = 2181
    protocol    = "tcp"
    cidr_blocks = [aws_vpc.main.cidr_block]
    description = "Allow Zookeeper client connections from within VPC"
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
  vpc_id                   = aws_vpc.main.id
  cidr_block               = "10.0.1.0/24"
  availability_zone        = "us-east-1a"  # Adjust as needed
  map_public_ip_on_launch  = true  # Enable automatic public IP assignment
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
  count                        = 5  # Create five EC2 instances
  ami                          = "ami-066784287e358dad1"  
  instance_type                = "t2.micro"
  key_name                     = "CoreCacheKey" 
  vpc_security_group_ids       = [aws_security_group.web_sg.id]
  subnet_id                    = aws_subnet.my_subnet.id  
  associate_public_ip_address  = true  # Ensure a public IP is assigned

  # User data script to install Python and Docker
  user_data = <<-EOF
              #!/bin/bash
              sudo yum update -y
              sudo yum install -y python3.11 jq
              sudo python3 -m ensurepip --upgrade
              sudo yum install -y docker
              sudo service docker start
              sudo systemctl enable docker
                
              # Verify Docker Compose installation
              docker compose version

              # Install docker compose 
              sudo curl -L https://github.com/docker/compose/releases/latest/download/docker-compose-Linux-x86_64 -o /usr/local/bin/docker-compose
              sudo chmod +x /usr/local/bin/docker-compose
              docker-compose version
              
              # Set environment variable for configuration
              echo 'ENV_FOR_DYNACONF=production' | sudo tee -a /etc/environment
              EOF

  tags = {
    Name = "core-cache-${count.index + 1}"
    type = lookup({
      0 = "leader",
      1 = "follower-1",
      2 = "follower-2",
      3 = "metrics",
      4 = "zookeeper"
    }, count.index, "unknown")
  }
}
