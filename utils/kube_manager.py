import asyncio
import json
import time
from asyncio import sleep

from kubernetes import client, config

import datetime

import pytz

DEPLOYMENT_NAME = "nginx-deployment"


def create_deployment_object(container_name="nginx", container_image="nginx:1.15.4",
                             resource_limits=None, resource_requests=None, template_labels=None, api_version="apps/v1",
                             replicas=1):
    """
    Creates a Kubernetes deployment object using the Kubernetes Python client.

    :param container_name: The name of the container. (Default: "nginx")
    :param container_image: The image for the container. (Default: "nginx:1.15.4")
    :param resource_limits: The resource limits for the container. (Default: {"cpu": "500m", "memory": "500Mi"})
    :param resource_requests: The resource requests for the container. (Default: {"cpu": "100m", "memory": "200Mi"})
    :param template_labels: The labels for the deployment template. (Default: {"app": "nginx"})
    :param api_version: The API version to use for the deployment. (Default: "apps/v1")
    :param replicas: The number of replicas to create. (Default: 1)

    :return: The created Kubernetes deployment object.
    """

    # Configurate Pod template container
    if template_labels is None:
        template_labels = {"app": "nginx"}
    if resource_requests is None:
        resource_requests = {"cpu": "100m", "memory": "200Mi"}
    if resource_limits is None:
        resource_limits = {"cpu": "500m", "memory": "500Mi"}

    container = client.V1Container(
        name=container_name,
        image=container_image,
        ports=[client.V1ContainerPort(container_port=80)],
        resources=client.V1ResourceRequirements(
            requests=resource_requests,
            limits=resource_limits,
        ),
    )

    # Create and configure a spec section
    template = client.V1PodTemplateSpec(
        metadata=client.V1ObjectMeta(labels=template_labels),
        spec=client.V1PodSpec(containers=[container]),
    )

    # Create the specification of deployment
    spec = client.V1DeploymentSpec(
        replicas=replicas, template=template, selector={
            "matchLabels":
                template_labels})

    # Instantiate the deployment object
    deployment = client.V1Deployment(
        api_version=api_version,
        kind="Deployment",
        metadata=client.V1ObjectMeta(name=DEPLOYMENT_NAME),
        spec=spec,
    )

    return deployment


def pods_metrics():
    # Load Kubernetes configuration from default location
    config.load_kube_config()

    # Create an instance of the Kubernetes API client

    api_client = client.ApiClient()
    custom_api = client.CustomObjectsApi(api_client)

    resp = custom_api.list_cluster_custom_object("metrics.k8s.io", "v1beta1", "pods")

    return resp["items"]


def nodes_metrics():
    # Load Kubernetes configuration from default location
    config.load_kube_config()

    # Create an instance of the Kubernetes API client

    api_client = client.ApiClient()
    custom_api = client.CustomObjectsApi(api_client)

    resp = custom_api.list_cluster_custom_object("metrics.k8s.io", "v1beta1", "nodes")

    return resp["items"]


def create_deployment(api, deployment):
    # Create deployment
    resp = api.create_namespaced_deployment(
        body=deployment, namespace="default"
    )

    return resp


def update_deployment(api, deployment, **kwargs):
    modified = False
    resp = None
    # Update container image
    for key, value in kwargs.items():
        if key == "container_image":
            deployment.spec.template.spec.containers[0].image = value
            modified = True
        elif key == "replicas":
            deployment.spec.replicas = value
            modified = True

    # patch the deployment
    if modified:
        resp = api.patch_namespaced_deployment(
            name=DEPLOYMENT_NAME, namespace="default", body=deployment
        )
    return deployment


def restart_deployment(api, deployment):
    # update `spec.template.metadata` section
    # to add `kubectl.kubernetes.io/restartedAt` annotation
    deployment.spec.template.metadata.annotations = {
        "kubectl.kubernetes.io/restartedAt": datetime.datetime.utcnow()
        .replace(tzinfo=pytz.UTC)
        .isoformat()
    }

    # patch the deployment
    resp = api.patch_namespaced_deployment(
        name=DEPLOYMENT_NAME, namespace="default", body=deployment
    )

    return resp


def delete_deployment(api):
    # Delete deployment
    resp = api.delete_namespaced_deployment(
        name=DEPLOYMENT_NAME,
        namespace="default",
        body=client.V1DeleteOptions(
            propagation_policy="Foreground", grace_period_seconds=5
        ),
    )
    return resp


def test():
    # Configs can be set in Configuration class directly or using helper
    # utility. If no argument provided, the config will be loaded from
    # default location.
    config.load_kube_config()
    apps_v1 = client.AppsV1Api()

    deployment = create_deployment_object()

    resp = create_deployment(apps_v1, deployment)
    print("\n[INFO] deployment `nginx-deployment` created.\n")
    print("%s\t%s\t\t\t%s\t%s" % ("NAMESPACE", "NAME", "REVISION", "IMAGE"))
    print(
        "%s\t\t%s\t%s\t\t%s\n"
        % (
            resp.metadata.namespace,
            resp.metadata.name,
            resp.metadata.generation,
            resp.spec.template.spec.containers[0].image,
        )
    )
    time.sleep(10)

    resp = update_deployment(apps_v1, deployment, replicas=5)
    print("\n[INFO] deployment's container image updated.\n")
    print("%s\t%s\t\t\t%s\t%s" % ("NAMESPACE", "NAME", "REVISION", "IMAGE"))
    print(
        "%s\t\t%s\t%s\t\t%s\n"
        % (
            resp.metadata.namespace,
            resp.metadata.name,
            resp.metadata.generation,
            resp.spec.template.spec.containers[0].image,
        )
    )

    resp = restart_deployment(apps_v1, deployment)
    print("\n[INFO] deployment `nginx-deployment` restarted.\n")
    print("%s\t\t\t%s\t%s" % ("NAME", "REVISION", "RESTARTED-AT"))
    print(
        "%s\t%s\t\t%s\n"
        % (
            resp.metadata.name,
            resp.metadata.generation,
            resp.spec.template.metadata.annotations,
        )
    )

    time.sleep(30)

    resp = delete_deployment(apps_v1)
    print("\n[INFO] deployment `nginx-deployment` deleted.")
