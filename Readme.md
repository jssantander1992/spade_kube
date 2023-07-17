# SPADE-Kubernetes Integration

This project demonstrates the integration of the SPADE framework with the Kubernetes Python client to manage deployments in a Kubernetes cluster. The project includes two parts: the SPADE agents that execute a Finite State Machine (FSM) and interact with Kubernetes, and the utility functions for managing Kubernetes deployments.

## Prerequisites

Before running the project, make sure you have the following dependencies installed:

- SPADE framework
- Kubernetes Python client
- Python 3.9 or higher
- Access to a Kubernetes cluster and valid configuration (for the Kubernetes Python client)

## Installation

1. Clone the project repository:

```
git clone <repository-url>
cd spade_kube
```

2. Create Virtual enviroment and activate it.
3. Install requirementes:
```
pip install -r requirementes.txt
```

## Usage

### SPADE Integration

To run the project with SPADE integration, follow these steps:

1. Configure the Kubernetes client:

   Make sure you have a valid Kubernetes configuration file (`kubeconfig`) or a valid `KUBECONFIG` environment variable set.

2. Update the agent configuration:

   Open the `main.py` file and modify the `user1` and `user2` dictionaries with the XMPP username and password of the agents.

3. Start the SPADE agents:

   Run the following command to start the agents:
```
python main.py
```
This will create a deployment, update its properties, restart it, and finally delete it.

## Contributing

Contributions to this project are welcome! If you find any issues or have suggestions for improvements, please open an issue or submit a pull request.

## License

This project is licensed under the [GNU](LICENSE).