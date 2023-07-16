import time
import random

from spade.agent import Agent
from spade.behaviour import FSMBehaviour, State, PeriodicBehaviour
from spade.message import Message

from utils.kube_manager import set_replicas

STATE_1 = "INIT"
STATE_2 = "READ_DATA"
STATE_3 = "MAKE_DECISION"
STATE_4 = "KUBE_ACTION"
STATE_5 = "END"


class kube_fsm(FSMBehaviour):
    async def on_start(self):
        print(f"FSM starting at initial state {self.current_state}")

    async def on_end(self):
        print(f"FSM finished at state {self.current_state}")
        await self.agent.stop()


class State1(State):
    async def run(self):
        print("I'm at state one (initial state)")
        self.set_next_state(STATE_2)


class State2(State):
    def __init__(self):
        self.data = ''

    async def run(self):
        print("RecvBehav running")

        msg = await self.receive(timeout=3)

        if msg:
            print("Message received with content: {}".format(msg.body))
            self.data = msg.body
            self.set_next_state(STATE_3)
        else:
            print("Did not received any message after 10 seconds")
            self.set_next_state(STATE_2)


class State3(State):
    async def run(self):
        print("I'm Making the desition")
        time.sleep(5)
        rand = random.randint(1, 100)

        if rand > 30:
            self.set_next_state(STATE_4)
        else:
            self.set_next_state(STATE_2)


class State4(State):
    async def run(self):
        print("acting on kube")

        rand = random.randint(1,10)

        await set_replicas(rand)

        msg = Message(to=str(self.agent.jid))
        msg.body = "Action done"
        await self.send(msg)

        rand = random.randint(1, 100)

        if rand > 95:
            self.set_next_state(STATE_5)
        else:
            self.set_next_state(STATE_2)


class State5(State):
    async def run(self):
        print("FINISH")


class FSMAgent(Agent):
    async def setup(self):
        fsm = kube_fsm()
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
            # time.sleep(5)
            rand = random.randint(1, 100)

            if rand > 20:
                msg = Message(to="user1@xmpp.jssdev.com")  # Instantiate the message
                msg.set_metadata("performative", "inform")  # Set the "inform" FIPA performative
                msg.body = "5"  # Set the message content
                await self.send(msg)
                print("Message sent!")

    async def setup(self):
        print("SenderAgent started")
        b = self.InformBehav(period=2)
        self.add_behaviour(b)
