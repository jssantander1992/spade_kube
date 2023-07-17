import spade

from utils.agents import FSMAgent, PeriodicAgent
from kubernetes import client, config
from utils.kube_manager import create_deployment_object, pods_metrics

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


if __name__ == "__main__":
    spade.run(main())

