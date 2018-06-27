import json

SIZE = 4096

# msg types
VERIFY = "verify"
SUCCESS = "success"
INVALID = "invalid"
TERMINATE = "terminate"

TRIAL_REQUEST = "request"
TRIAL_DETAILS = "details"
TRIAL_DONE = "done"
TRIAL_CANCEL = "cancel"
TRIAL_SEND = "send"
TRIAL_DATA = "data"

def serialize(data):
    if isinstance(data, dict):
        return bytes(json.dumps(data), 'ascii')
    else:
        raise TypeError("data needs to have type 'dict'")

def deserialize(data):
    if isinstance(data, bytes):
        if len(data) != 0:
            return json.loads(str(data, 'ascii'))
        else:
            return None
    else:
        raise TypeError("data needs to have type 'bytes'")
