from federated_core.client import FederatedClient

client = FederatedClient("data/federated/client_1.csv")
weights, metrics = client.train(epochs=8)

print(metrics)