# Kubernetes (Minikube) deployment

## Prerequisites

- Minikube installed and started: `minikube start`
- Ingress addon: `minikube addons enable ingress`
- kubectl configured for the cluster

## 1. Create secret

```bash
cp base/secret.yaml.example base/secret.yaml
# Edit base/secret.yaml: set DATABASE_URL (use host.minikube.internal as DB host), JWT_SECRET_KEY
# Do not commit base/secret.yaml
```

## 2. Build images inside Minikube

So the cluster can use local images (no registry).

**Linux/macOS (bash):**
```bash
eval $(minikube docker-env)
# From project root (cursor_test):
make build-images
```

**Windows (PowerShell):**
```powershell
minikube -p minikube docker-env | Invoke-Expression
# Then from cursor_test run the build commands, or use: .\k8s\build-images.ps1
```

Or run from project root:
```bash
docker build -t gateway:latest ./api-gateway
docker build -t auth:latest ./auth
docker build -t core:latest ./core
docker build -t scheduler:latest ./scheduler
docker build -t ui:latest ./ui-app
docker build -t tg-bot:latest ./tg-bot
docker build -t wp-bot:latest ./wp-bot
docker build -t url-bot:latest ./url-bot
docker build -t collector:latest ./collector
docker build -t processor:latest ./processor
docker build -t th-bot:latest ./th-bot
docker build -t selectcb:latest ./selectcb
```

## 3. Apply manifests

**With Make (Linux/macOS):**
```bash
make apply-all
```

**Manually:**
```bash
kubectl apply -f k8s/base/namespace.yaml
kubectl apply -f k8s/base/secret.yaml
kubectl apply -f k8s/tg-bot/pvc.yaml
kubectl apply -f k8s/gateway/
kubectl apply -f k8s/auth/
kubectl apply -f k8s/core/
kubectl apply -f k8s/scheduler/
kubectl apply -f k8s/ui/
kubectl apply -f k8s/tg-bot/
kubectl apply -f k8s/wp-bot/
kubectl apply -f k8s/url-bot/
kubectl apply -f k8s/collector/
kubectl apply -f k8s/processor/
kubectl apply -f k8s/th-bot/
kubectl apply -f k8s/selectcb/
kubectl apply -f k8s/ingress.yaml
```

## 4. Access the app

- Ingress: get Minikube IP with `minikube ip`. Use that IP as host (e.g. add to `/etc/hosts` or use `http://<minikube-ip>.nip.io`) and open `http://<host>/` for UI; API is at `http://<host>/api/...`.
- Or port-forward for quick test: `kubectl port-forward -n app svc/gateway 8000:8000` and `kubectl port-forward -n app svc/ui 8100:8100` (UI must call API at same origin or configure CORS).

## 5. Check pods

```bash
kubectl get pods -n app
kubectl logs -n app deployment/gateway -f
```

## External PostgreSQL

Secret must set `DATABASE_URL` with host `host.minikube.internal` (or the host IP) so pods in Minikube can reach PostgreSQL on the host. Ensure PostgreSQL listens on a interface reachable from the cluster (e.g. 0.0.0.0).
