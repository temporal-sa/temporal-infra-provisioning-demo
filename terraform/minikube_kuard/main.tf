terraform {
  required_providers {
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.27.0"
    }
  }
}

provider "kubernetes" {
  config_path    = "~/.kube/config"
  config_context = "minikube"
}

resource "kubernetes_namespace" "kuard" {
  metadata {
    name = "kuard-namespace"
  }
}

resource "kubernetes_deployment" "kuard" {
  metadata {
    name      = "kuard"
    namespace = kubernetes_namespace.kuard.metadata[0].name
    labels = {
      app = "kuard"
    }
  }

  spec {
    replicas = 1

    selector {
      match_labels = {
        app = "kuard"
      }
    }

    template {
      metadata {
        labels = {
          app = "kuard"
        }
      }

      spec {
        container {
          image = "gcr.io/kuar-demo/kuard-amd64:blue"
          name  = "kuard"

          port {
            container_port = 8080
          }

          resources {
            limits = {
              cpu    = "200m"
              memory = "256Mi"
            }
            requests = {
              cpu    = "100m"
              memory = "128Mi"
            }
          }
        }
      }
    }
  }
}

resource "kubernetes_service" "kuard" {
  metadata {
    name      = "kuard"
    namespace = kubernetes_namespace.kuard.metadata[0].name
  }

  spec {
    selector = {
      app = "kuard"
    }

    port {
      port        = 80
      target_port = 8080
    }

    type = "NodePort"
  }
}
