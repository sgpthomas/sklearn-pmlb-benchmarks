import json

# payload size
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

# debugging
DEBUG = False
def debug(s):
    if DEBUG: print(s)

def serialize(data):
    '''Serializes a dictionary into json bytes'''
    if isinstance(data, dict):
        debug("<- {}".format(data))
        return bytes(json.dumps(data), 'ascii')
    else:
        raise TypeError("data needs to have type 'dict'")

def deserialize(data):
    ''' Takes a json byte string and returns a list of dictionaries.
    This function returns a list because sometimes we get multiple payloads
    in one packet.
    '''
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
                debug("-> [{}] {}".format(len(results), results))
                return results
            else:
                return None
        else:
            raise TypeError("data needs to have type 'bytes'")
    except json.decoder.JSONDecodeError:
        print("Error Decoding!")
        print(data)
