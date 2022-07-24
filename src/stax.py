
from json import dumps
from utils import get_stax_client

def lambda_handler():
    workloads_client = get_stax_client("workloads")

    response = workloads_client.ReadWorkloads()
    print(dumps(response, indent=4, sort_keys=True))

lambda_handler()
