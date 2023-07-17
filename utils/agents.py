import json
import time
import random
from enum import Enum

from spade.agent import Agent
from spade.behaviour import FSMBehaviour, State, PeriodicBehaviour
from spade.message import Message

from utils.kube_manager import create_deployment, delete_deployment, update_deployment, pods_metrics, nodes_metrics, \
    create_deployment_object

STATE_1 = "INIT"
STATE_2 = "READ_DATA"
STATE_3 = "MAKE_DECISION"
STATE_4 = "KUBE_ACTION"
STATE_5 = "END"


class Action(Enum):
    KEEP = 1
    INCREASE_REPLICA = 2
    DECREASE_REPLICA = 3
    FINISH = 4


def make_desition(deployment, pods, nodes):
    rand = random.randint(1, 100)

    replicas = deployment.spec.replicas
    if (rand < 25 and replicas != 1):
        return Action.DECREASE_REPLICA
    elif 75 < rand <= 100 and replicas < 10:
        return Action.INCREASE_REPLICA
    elif rand > 100:
        return Action.FINISH
    return Action.KEEP


class KubeFSM(FSMBehaviour):

    async def on_start(self):
        print(f"FSM starting at initial state {self.current_state}")

    async def on_end(self):
        print(f"FSM finished at state {self.current_state}")
        await self.agent.stop()


class State1(State):
    async def run(self):
        print("-------------------------------------------------------")
        print(f"STATE-1:{STATE_1}")
        resp = create_deployment(self.agent.app, self.agent.deployment)
        print(f"[INFO] deployment `{resp.metadata.name}` created.")
        print("-------------------------------------------------------")
        self.set_next_state(STATE_2)


class State2(State):
    async def run(self):
        print("-------------------------------------------------------")
        print(f"STATE-2:{STATE_2}")

        msg = await self.receive(timeout=10)

        if msg:
            print(msg.body)
            data = json.loads(msg.body)
            pods = data["pods"]
            self.agent.pods = list(filter(lambda value: "'nginx-deployment" in value, pods))
            self.agent.nodes = data["nodes"]
            self.set_next_state(STATE_3)
        else:
            print("Did not received any message after 10 seconds")
            self.set_next_state(STATE_2)
        print("-------------------------------------------------------")


class State3(State):
    async def run(self):
        print("-------------------------------------------------------")
        print(f"STATE-3:{STATE_3}")
        time.sleep(5)

        self.agent.action = make_desition(self.agent.deployment, self.agent.pods, self.agent.nodes)

        if self.agent.action != Action.KEEP:
            self.set_next_state(STATE_4)
        else:
            self.set_next_state(STATE_2)
        print(f"Action: {self.agent.action}")
        print("-------------------------------------------------------")


class State4(State):
    async def run(self):
        print("-------------------------------------------------------")
        print(f"STATE-4:{STATE_4}")

        if self.agent.action == Action.FINISH:
            self.set_next_state(STATE_5)
        else:
            if self.agent.action == Action.INCREASE_REPLICA:
                replicas = self.agent.deployment.spec.replicas + 1
                print(f"New number od replicas={replicas}")
                self.agent.deployment = update_deployment(self.agent.app, self.agent.deployment, replicas=replicas)
            elif self.agent.action == Action.DECREASE_REPLICA:
                replicas = self.agent.deployment.spec.replicas - 1
                print(f"New number od replicas={replicas}")
                self.agent.deployment = update_deployment(self.agent.app, self.agent.deployment, replicas=replicas)

            self.set_next_state(STATE_2)

        print("-------------------------------------------------------")


class State5(State):
    async def run(self):
        resp = delete_deployment(self.agent.app)
        print("FINISH")


class FSMAgent(Agent):
    app = None
    deployment = None
    pods = None
    nodes = None
    action = None

    async def setup(self):
        fsm = KubeFSM()
        fsm.app = self.app
        fsm.deployment = self.deployment
        fsm.add_state(name=STATE_1, state=State1(), initial=True)
        fsm.add_state(name=STATE_2, state=State2())
        fsm.add_state(name=STATE_3, state=State3())
        fsm.add_state(name=STATE_4, state=State4())
        fsm.add_state(name=STATE_5, state=State5())
        fsm.add_transition(source=STATE_1, dest=STATE_2)
        fsm.add_transition(source=STATE_2, dest=STATE_3)
        fsm.add_transition(source=STATE_2, dest=STATE_2)
        fsm.add_transition(source=STATE_3, dest=STATE_4)
        fsm.add_transition(source=STATE_3, dest=STATE_2)
        fsm.add_transition(source=STATE_4, dest=STATE_2)
        fsm.add_transition(source=STATE_4, dest=STATE_5)
        self.add_behaviour(fsm)


class PeriodicAgent(Agent):
    class InformBehav(PeriodicBehaviour):
        async def run(self):
            print("+++++++++++++++++++++++++++++++++++++++++++++++++++++++")
            print("Periodic")
            # time.sleep(5)
            mesg = {}

            pods = pods_metrics()
            mesg["pods"] = pods

            nodes = nodes_metrics()
            mesg["nodes"] = nodes

            msg = Message(to="user1@xmpp.jssdev.com")  # Instantiate the message
            msg.set_metadata("performative", "inform")  # Set the "inform" FIPA performative
            msg.body = json.dumps(mesg)  # Set the message content
            await self.send(msg)
            print("Message sent!")
            print("+++++++++++++++++++++++++++++++++++++++++++++++++++++++")

    async def setup(self):
        print("SenderAgent started")
        b = self.InformBehav(period=2)
        self.add_behaviour(b)
