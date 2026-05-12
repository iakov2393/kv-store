# Key-Value Store (mini Redis) on gRPC

## Setup

```bash
pip install -r requirements.txt
python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. kvstore.proto
```

## Run

```bash
python server.py
```

Server listens on port **8000**.

## Quick test (grpcurl)

```bash
# Put
grpcurl -plaintext -d '{"key":"foo","value":"bar","ttl_seconds":60}' localhost:8000 kvstore.KeyValueStore/Put

# Get
grpcurl -plaintext -d '{"key":"foo"}' localhost:8000 kvstore.KeyValueStore/Get

# List
grpcurl -plaintext -d '{"prefix":"fo"}' localhost:8000 kvstore.KeyValueStore/List

# Delete
grpcurl -plaintext -d '{"key":"foo"}' localhost:8000 kvstore.KeyValueStore/Delete
```