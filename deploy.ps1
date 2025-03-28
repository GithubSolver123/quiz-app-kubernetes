# Deployment script for Quiz App on Minikube with 2 nodes (Docker driver)

# Step 1: Start 2-node Minikube cluster
Write-Host "Starting 2-node Minikube cluster..." -ForegroundColor Green
minikube delete
minikube start --nodes=2 --memory=2048 --cpus=2 --driver=docker

# Step 2: Verify nodes are ready
Write-Host "Verifying nodes are ready..." -ForegroundColor Green
kubectl get nodes

# Step 3: Enable registry addon
Write-Host "Enabling registry addon..." -ForegroundColor Green
minikube addons enable registry
minikube addons enable metrics-server

# Step 4: Setup port forwarding for registry
Write-Host "Setting up port forwarding for registry..." -ForegroundColor Green
$registryPod = kubectl get pods -n kube-system -l kubernetes.io/minikube-addons=registry -o jsonpath='{.items[0].metadata.name}'
Start-Process -NoNewWindow -FilePath "kubectl" -ArgumentList "port-forward --namespace kube-system $registryPod 57913:5000"

# Step 5: Build and push Docker image
Write-Host "Building and pushing Docker image..." -ForegroundColor Green
docker build -t localhost:57913/quiz-app:v1 .
docker push localhost:57913/quiz-app:v1

# Step 6: Apply Kubernetes configs
Write-Host "Applying Kubernetes configurations..." -ForegroundColor Green
kubectl apply -f k8s/pv-pvc.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secret.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/hpa.yaml

# Step 7: Check deployment status
Write-Host "Checking deployment status..." -ForegroundColor Green
kubectl get all

# Step 8: Display access information
Write-Host "Getting service URL..." -ForegroundColor Green
minikube service quiz-app-service --url

Write-Host "Deployment complete! Access your application at the URL above." -ForegroundColor Green
Write-Host "Run 'kubectl get pods' to check pod status" -ForegroundColor Green
Write-Host "Run 'kubectl logs <pod-name>' to check logs" -ForegroundColor Green 