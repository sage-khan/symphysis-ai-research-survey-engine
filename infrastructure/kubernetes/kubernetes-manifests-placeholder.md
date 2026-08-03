# Kubernetes manifests: not yet implemented

Symphysis currently deploys as a single Docker container on the host
network plus a plain `nohup`'d Vite dev server (see the README's
"Deploying on a shared server" section); there is no Kubernetes
deployment yet. This directory is reserved for that manifest set
(Deployment, Service, ConfigMap for `config/defaults.yaml`, a
PersistentVolumeClaim for `surveys/` and `agents_library/`) once a
Kubernetes deployment target actually exists. See the README's "Future
enhancements" section for the current deployment-shape roadmap.
