import asyncio
from asyncio import sleep

from kubernetes import client, config


def list_pods():
    config.load_kube_config()

    v1 = client.CoreV1Api()
    print("Listing pods with their IPs:")
    ret = v1.list_pod_for_all_namespaces(watch=False)

    for i in ret.items:
        print("%s\t%s\t%s" % (i.status.pod_ip, i.metadata.namespace, i.metadata.name))


def set_replicas(replicas: int, deployment_name="wordpress", namespace="default"):
    print("================================================================")
    print("Starting Action")
    config.load_kube_config()

    k8s_client = client.ApiClient()

    body = {
        "spec": {
            "replicas": replicas
        }
    }

    api_instance = client.AppsV1Api(k8s_client)
    response = api_instance.patch_namespaced_deployment(
        name=deployment_name,
        namespace=namespace,
        body=body
    )

    get_replicas()

    if response.status.replicas == replicas:
        print("Deployment replicas updated successfully.")
    else:
        print("Failed to update deployment replicas.")

    print("================================================================")


def get_replicas(deployment_name="wordpress", namespace="default"):
    config.load_kube_config()

    k8s_client = client.ApiClient()

    api_instance = client.AppsV1Api(k8s_client)
    response = api_instance.read_namespaced_deployment(
        name=deployment_name,
        namespace=namespace
    )

    return response.spec.replicas
