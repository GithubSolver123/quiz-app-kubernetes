# Quiz App Kubernetes Deployment

A comprehensive deployment of a Flask-based Quiz Application on Kubernetes, featuring user roles, quiz management, and automated testing capabilities.

## Project Overview

This project demonstrates deploying a scalable web application using Kubernetes. The application is a quiz platform that supports:

- Different user roles (admin, teacher, student)
- Quiz creation and management
- Timed quiz sessions
- Results tracking and analytics
- Persistent data storage

## Technologies Used

- **Backend**: Python Flask
- **Database**: SQLite with persistent storage
- **Containerization**: Docker
- **Orchestration**: Kubernetes (Minikube)
- **Authentication**: Flask-Login

## Prerequisites

- Docker Desktop
- Minikube
- kubectl
- Python 3.9+
- PowerShell (for Windows) or Bash (for Linux/macOS)

## Deployment Architecture

The application is deployed with the following Kubernetes resources:

- **Deployment**: 3 replicas of the Quiz App container
- **Service**: NodePort service exposing the application
- **ConfigMap**: Environment variables configuration
- **Secret**: Sensitive data storage (credentials, keys)
- **PersistentVolume & PVC**: For database persistence
- **HorizontalPodAutoscaler**: Auto-scales based on CPU utilization (2-5 pods)

## Quick Start

### 1. Clone the repository
```bash
git clone https://github.com/yourusername/quiz-app-kubernetes.git
cd quiz-app-kubernetes
```

### 2. Start Minikube
```bash
minikube start --memory=2048 --cpus=2 --driver=docker
```

### 3. Configure Docker to use Minikube's daemon
```bash
# For PowerShell
& minikube -p minikube docker-env | Invoke-Expression
```

### 4. Build the Docker image
```bash
docker build -t quiz-app:v1 .
```

### 5. Deploy the application
```bash
# Apply Kubernetes manifests
kubectl apply -f k8s/pv-pvc.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secret.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/hpa.yaml

# Enable metrics-server for HPA
minikube addons enable metrics-server
```

### 6. Access the application
```bash
minikube service quiz-app-service --url
```

### 7. Automated deployment
Alternatively, run the provided deployment script:
```bash
# For PowerShell
.\deploy.ps1
```

## Testing Scenarios

### 1. Application Availability Test
```bash
# Check if the service is available
kubectl get services

# Test application endpoint
minikube service quiz-app-service --url
```

### 2. Scaling Test
```bash
# Watch the HPA
kubectl get hpa -w

# Generate load in another terminal
kubectl run --rm -it --image=busybox load-generator -- /bin/sh -c "while true; do wget -q -O- http://quiz-app-service; done"

# Watch the pods increase
kubectl get pods -w
```

### 3. Rolling Update Test
```bash
# Build a new version
docker build -t quiz-app:v2 .

# Perform a rolling update
kubectl set image deployment/quiz-app quiz-app=quiz-app:v2

# Check rollout status
kubectl rollout status deployment/quiz-app
```

### 4. Rollback Test
```bash
# Rollback to previous version
kubectl rollout undo deployment/quiz-app

# Check rollback status
kubectl rollout status deployment/quiz-app
```

### 5. Pod Failure and Self-Healing Test
```bash
# Delete a pod and watch Kubernetes recreate it
kubectl delete pod $(kubectl get pods -l app=quiz-app -o jsonpath="{.items[0].metadata.name}")
kubectl get pods -w
```

### 6. Persistent Storage Test
```bash
# Create data, delete pod, verify data persists after pod recreation
```

### 7. Logging Test
```bash
# View application logs
kubectl logs $(kubectl get pods -l app=quiz-app -o jsonpath="{.items[0].metadata.name}")
```

## Application Usage

### Default Admin Credentials
- Username: `admin`
- Password: `admin123`

### User Roles
1. **Administrator**: Manages users (add/remove teachers and students)
2. **Teacher**: Creates quizzes, views results, analyzes performance
3. **Student**: Takes quizzes, views personal history and scores

## Kubernetes Files Explained

- **deployment.yaml**: Defines the application deployment with 3 replicas
- **service.yaml**: Exposes the application via NodePort
- **configmap.yaml**: Stores environment variables
- **secret.yaml**: Stores sensitive data (encoded)
- **pv-pvc.yaml**: Defines persistent storage for the database
- **hpa.yaml**: Configures auto-scaling based on CPU utilization

## Cleanup

```bash
# Delete all resources
kubectl delete -f k8s/
# OR
kubectl delete all --all

# Stop Minikube
minikube stop
```

## Project Structure
```
quiz-app-kubernetes/
├── app.py                  # Main Flask application
├── requirements.txt        # Python dependencies
├── Dockerfile              # Container definition
├── .dockerignore           # Docker build exclusions
├── deploy.ps1              # Deployment automation
├── templates/              # HTML templates
├── k8s/                    # Kubernetes manifests
│   ├── deployment.yaml
│   ├── configmap.yaml
│   ├── secret.yaml
│   ├── pv-pvc.yaml
│   └── hpa.yaml
```

## Troubleshooting

**Issue**: Pods stuck in Pending state
**Solution**: Check PersistentVolume provisioning or resource constraints

**Issue**: HPA not scaling pods
**Solution**: Verify metrics-server is enabled (`minikube addons enable metrics-server`)

**Issue**: Cannot access application
**Solution**: Ensure service is properly configured and use `minikube service quiz-app-service`

## References

- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Minikube Documentation](https://minikube.sigs.k8s.io/docs/)
- [Flask Documentation](https://flask.palletsprojects.com/)
