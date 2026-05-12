import threading
import time
from collections import OrderedDict
from concurrent import futures

import grpc

import kvstore_pb2
import kvstore_pb2_grpc

MAX_KEYS = 10


class LRUStore:
    def __init__(self, capacity: int = MAX_KEYS):
        self.capacity = capacity
        self.lock = threading.Lock()
        self._store: OrderedDict = OrderedDict()

    def _is_expired(self, expire_at) -> bool:
        return expire_at is not None and time.monotonic() > expire_at

    def put(self, key: str, value: str, ttl_seconds: int):
        expire_at = time.monotonic() + ttl_seconds if ttl_seconds > 0 else None
        with self.lock:
            if key in self._store:
                self._store.move_to_end(key)
            self._store[key] = (value, expire_at)
            while len(self._store) > self.capacity:
                self._store.popitem(last=False)

    def get(self, key: str):
        with self.lock:
            if key not in self._store:
                return None
            value, expire_at = self._store[key]
            if self._is_expired(expire_at):
                del self._store[key]
                return None
            self._store.move_to_end(key)
            return value

    def delete(self, key: str):
        with self.lock:
            self._store.pop(key, None)

    def list_prefix(self, prefix: str):
        result = []
        now = time.monotonic()
        with self.lock:
            for key, (value, expire_at) in list(self._store.items()):
                if expire_at is not None and now > expire_at:
                    continue
                if key.startswith(prefix):
                    result.append((key, value))
        return result


class KeyValueStoreServicer(kvstore_pb2_grpc.KeyValueStoreServicer):
    def __init__(self):
        self.store = LRUStore()

    def Put(self, request, context):
        self.store.put(request.key, request.value, request.ttl_seconds)
        return kvstore_pb2.PutResponse()

    def Get(self, request, context):
        value = self.store.get(request.key)
        if value is None:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details(f"Key '{request.key}' not found or expired")
            return kvstore_pb2.GetResponse()
        return kvstore_pb2.GetResponse(value=value)

    def Delete(self, request, context):
        self.store.delete(request.key)
        return kvstore_pb2.DeleteResponse()

    def List(self, request, context):
        items = self.store.list_prefix(request.prefix)
        kv_items = [kvstore_pb2.KeyValue(key=k, value=v) for k, v in items]
        return kvstore_pb2.ListResponse(items=kv_items)


def serve():
    grpc_server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    kvstore_pb2_grpc.add_KeyValueStoreServicer_to_server(
        KeyValueStoreServicer(), grpc_server
    )
    grpc_server.add_insecure_port("[::]:8000")
    grpc_server.start()
    print("Server started on port 8000")
    grpc_server.wait_for_termination()


if __name__ == "__main__":
    serve()
