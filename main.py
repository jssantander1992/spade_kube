import asyncio
import getpass
import time

import spade

from utils.agents import FSMAgent, PeriodicAgent
from kubernetes import client, config
from utils.kube_manager import create_deployment_object, create_deployment, \
    update_deployment, restart_deployment, delete_deployment

user1 = {"username": "user1@xmpp.jssdev.com", "pass": "jss12345"}
user2 = {"username": "user2@xmpp.jssdev.com", "pass": "jss12345"}


async def main():
    config.load_kube_config()
    apps_v1 = client.AppsV1Api()
    deployment = create_deployment_object()

    fsmagent = FSMAgent(user1["username"], user1["pass"])
    fsmagent.app = apps_v1
    fsmagent.deployment = deployment

    periodicagent = PeriodicAgent(user2["username"], user2["pass"])

    await fsmagent.start()
    await periodicagent.start()
    fsmagent.web.start(hostname="127.0.0.1", port="10000")

    await spade.wait_until_finished(fsmagent)
    await fsmagent.stop()
    await periodicagent.stop()
    print("Agent finished")


def main2():
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


if __name__ == "__main__":
    spade.run(main())

    # main2()
