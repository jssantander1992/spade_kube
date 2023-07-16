import asyncio
import getpass

import spade

from utils.agents import FSMAgent, PeriodicAgent
from utils.kube_manager import set_replicas, get_replicas

user1 = {"username": "user1@xmpp.jssdev.com", "pass": "jss12345"}
user2 = {"username": "user2@xmpp.jssdev.com", "pass": "jss12345"}


async def main():
    fsmagent = FSMAgent(user1["username"], user1["pass"])
    periodicagent = PeriodicAgent(user2["username"], user2["pass"])

    await fsmagent.start()
    await  periodicagent.start()
    fsmagent.web.start(hostname="127.0.0.1", port="10000")

    await spade.wait_until_finished(fsmagent)
    await fsmagent.stop()
    print("Agent finished")


if __name__ == "__main__":
    spade.run(main())
    # print(get_replicas())