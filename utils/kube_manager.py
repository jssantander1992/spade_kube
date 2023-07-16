import asyncio
from asyncio import sleep

from kubernetes import client, config

import datetime

import pytz

DEPLOYMENT_NAME = "nginx-deployment"


def create_deployment_object(container_name="nginx", container_image="nginx:1.15.4",
                             resource_limits=None, resource_requests=None, template_labels=None, api_version="apps/v1"):
    """
    Creates a Kubernetes deployment object using the Kubernetes Python client.

    :param container_name: The name of the container. (Default: "nginx")
    :param container_image: The image for the container. (Default: "nginx:1.15.4")
    :param resource_limits: The resource limits for the container. (Default: {"cpu": "500m", "memory": "500Mi"})
    :param resource_requests: The resource requests for the container. (Default: {"cpu": "100m", "memory": "200Mi"})
    :param template_labels: The labels for the deployment template. (Default: {"app": "nginx"})
    :param api_version: The API version to use for the deployment. (Default: "apps/v1")

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
        replicas=1, template=template, selector={
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
    return resp


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
