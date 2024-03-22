import netsquid as ns
import netsquid.qubits.qubitapi as qapi
import netsquid.qubits.operators as ns_ops
import numpy as np
from netsquid.nodes import Node
from netsquid.components import QuantumMemory
from netsquid.components.models import DelayModel
from netsquid.components.models.qerrormodels import QuantumErrorModel
from netsquid.components import QuantumChannel
from netsquid.nodes import DirectConnection
from netsquid.protocols import NodeProtocol


#DEFINE A CUSTOM CLASS THAT MODELS A BIT FLIP
class BitFlipErrorModel(QuantumErrorModel):
    def __init__(self, error_probability):
        super().__init__()
        self.add_property(name="error_probability", value=error_probability)

    def error_operation(self, qubits, **kwargs):
        for qubit in qubits:
            # Use NetSquid's random number generator for repeatability
            if np.random.random() < self.properties["error_probability"]:
                qapi.operate(qubit, ns_ops.X)

#DEFINE A CUSTOM CLASS THAT MODELS A CERTAIN TRANSMISSION DELAY
class PingPongDelayModel(DelayModel):
    def __init__(self, speed_of_light_fraction=0.5, standard_deviation=0.05):
        super().__init__()
        self.properties["speed"] = speed_of_light_fraction * 3e5
        self.properties["std"] = standard_deviation
        self.required_properties = ['length'] #In km #not directly used but listed as a requirement from the model

    #takes a random speed from a normal distribution using a RNG from the DelayModel class
    def generate_delay(self, **kwargs):
        avg_speed = self.properties["speed"]
        std = self.properties["std"]
        speed = self.properties["rng"].normal(avg_speed, avg_speed * std)
        delay = 1e9 * kwargs['length'] / speed #Nanoseconds
        return delay
#SETTING UP NODES IN THE NETWORK WITH QUANTUM MEMORY

ping_qmemory = QuantumMemory("PingMemory", num_positions=3)
node_ping = Node(name="Ping", qmemory=ping_qmemory)

pong_qmemory = QuantumMemory("PongMemory", num_positions=3)
node_pong = Node(name="Pong", qmemory=pong_qmemory)

#CREATE QUANTUM CHANNELS Using the length of a standard ping pong table 2.74 m

distance = 2.74 / 1000 #default length units are km
delay_model = PingPongDelayModel()
noise_model = BitFlipErrorModel(error_probability=0.1)
channel_1 = QuantumChannel(name="channel[ping to pong]",
                           length=distance,
                           models={"delay_model": delay_model, "quantum_noise_model": noise_model}) #can include other models e.g. error or loss models
channel_2 = QuantumChannel(name="channel[pong to ping]",
                           length=distance,
                           models={"delay_model": delay_model, "quantum_noise_model": noise_model})

#WRAP THE TWO CHANNELS INTO ONE COMPONENT VIA THE DirectConnection CLASS
connection = DirectConnection(name="[PingPong]",
                              channel_AtoB=channel_1,
                              channel_BtoA=channel_2)
node_ping.connect_to(remote_node=node_pong, connection=connection,
                     local_port_name="qubitIO", remote_port_name="qubitIO") #they share name for simplification

#WE ESTABLISH THE RULES OF THE GAME FROM THE NodeProtocol BASE CLASS

class PingPongProtocol(NodeProtocol):
    def __init__(self, node, observable, qubit=None):
        super().__init__(node)
        self.observable = observable
        self.qubit = qubit
        # Define matching pair of strings for pretty printing of basis states:
        self.basis = ["|0>", "|1>"] if observable == ns.Z else ["|+>", "|->"]

    def run(self):
        if self.qubit is not None:
            # Move the qubit into quantum memory before sending
            self.node.qmemory.put(qubits=[self.qubit], positions=[0])
            # Immediately pop the qubit from memory to send
            qubit_to_send = self.node.qmemory.pop(positions=[0])[0]
            # Send (TX) qubit to the other node via port's output
            self.node.ports["qubitIO"].tx_output(qubit_to_send)
        while True:
            # Wait (yield) until input has arrived at port
            yield self.await_port_input(self.node.ports["qubitIO"])
            # Receive (RX) qubit on the port's input
            message = self.node.ports["qubitIO"].rx_input()
            qubit = message.items[0]
            # Move the received qubit into quantum memory
            self.node.qmemory.put(qubits=[qubit], positions=[0])
            print(f"{ns.sim_time():5.1f}: {self.node.name} stored quantum state in position 0")
            # Pop the qubit from memory for measurement and sending
            qubit_to_measure_and_send = self.node.qmemory.pop(positions=[0])[0]
            meas, prob = ns.qubits.measure(qubit_to_measure_and_send, observable=self.observable)
            print(f"{ns.sim_time():5.1f}: {self.node.name} measured "
                  f"{self.basis[meas]} with probability {prob:.2f}")
            # Send (TX) qubit to the other node via connection
            self.node.ports["qubitIO"].tx_output(qubit_to_measure_and_send)

#ASSIGN THE PROTOCOL TO BOTH NODES

qubits = ns.qubits.create_qubits(1)
ping_protocol = PingPongProtocol(node_ping, observable=ns.Z, qubit=qubits[0])
pong_protocol = PingPongProtocol(node_pong, observable=ns.Z)

ping_protocol.start()
pong_protocol.start()
run_stats = ns.sim_run(duration=1000)