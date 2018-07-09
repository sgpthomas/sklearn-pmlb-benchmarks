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
        # print("<- {}".format(data))
        return bytes(json.dumps(data), 'ascii')
    else:
        raise TypeError("data needs to have type 'dict'")

def deserialize(data):
    try:
        if isinstance(data, bytes):
            if len(data) != 0:
                data = str(data, 'ascii')
                split = data.split('}{')
                for i, s in enumerate(split):
                    if not s.startswith('{'): split[i] = '{' + split[i]
                    if not s.endswith('}'): split[i] += '}'

                results = []
                for s in split:
                    results.append(json.loads(s))

                # reverse so that the order is correct (last should be processed first)
                results.reverse()
                # print("-> [{}] {}".format(len(results), results))
                return results
            else:
                return None
        else:
            raise TypeError("data needs to have type 'bytes'")
    except json.decoder.JSONDecodeError:
        print("Error Decoding!")
        print(data)
