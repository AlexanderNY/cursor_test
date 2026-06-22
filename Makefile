# Kubernetes / Minikube targets. Run from cursor_test (project root).
# Prerequisites: minikube start, minikube addons enable ingress

SHELL := /bin/bash
K8S_DIR := k8s

# Use Minikube's Docker daemon so images are available in the cluster
minikube-docker:
	eval $$(minikube docker-env) && docker info | grep -q "minikube" && echo "Using Minikube Docker"

# Build all images (run after: eval $(minikube docker-env))
build-images: minikube-docker
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

# Apply base (namespace; ensure secret.yaml exists from secret.yaml.example)
apply-base:
	kubectl apply -f $(K8S_DIR)/base/namespace.yaml
	@test -f $(K8S_DIR)/base/secret.yaml || (echo "Create $(K8S_DIR)/base/secret.yaml from secret.yaml.example and run again"; exit 1)
	kubectl apply -f $(K8S_DIR)/base/secret.yaml

# Apply all manifests in dependency order
apply-all: apply-base
	kubectl apply -f $(K8S_DIR)/tg-bot/pvc.yaml
	kubectl apply -f $(K8S_DIR)/gateway
	kubectl apply -f $(K8S_DIR)/auth
	kubectl apply -f $(K8S_DIR)/core
	kubectl apply -f $(K8S_DIR)/scheduler
	kubectl apply -f $(K8S_DIR)/ui
	kubectl apply -f $(K8S_DIR)/tg-bot
	kubectl apply -f $(K8S_DIR)/wp-bot
	kubectl apply -f $(K8S_DIR)/url-bot
	kubectl apply -f $(K8S_DIR)/collector
	kubectl apply -f $(K8S_DIR)/processor
	kubectl apply -f $(K8S_DIR)/th-bot
	kubectl apply -f $(K8S_DIR)/selectcb
	kubectl apply -f $(K8S_DIR)/ingress.yaml

# Full deploy: build images then apply (after creating secret.yaml)
deploy: build-images apply-all

.PHONY: minikube-docker build-images apply-base apply-all deploy
