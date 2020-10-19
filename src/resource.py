import json
import hashlib

import boto3

import requests


def sendResponse(event, context, status, message, data={}):
    body = json.dumps({
        "Status": status,
        "Reason": message,
        "StackId": event['StackId'],
        "RequestId": event['RequestId'],
        "LogicalResourceId": event['LogicalResourceId'],
        "PhysicalResourceId": event['LogicalResourceId'] + '-'
            + hashlib.sha1(event['StackId'].encode()).hexdigest(),
        "Data": data,
    })

    requests.put(event['ResponseURL'], headers={'Content-Type': ''}, data=body)


def execute(action, properties={}):

    if not isinstance(action, str):
        if isinstance(action, list):
            for step in action:
                if not isinstance(step, dict):
                    return "FAILED", "Unexpected action element format", {}

                if "Action" not in step:
                    return "FAILED", "Missing 'Action' element (list)", {}

                status, message, data = execute(step["Action"],
                                                step.get("Parameters", {}))
                if status != "SUCCESS":
                    break
        elif isinstance(action, dict):
            if "Action" not in action:
                return "FAILED", "Missing 'Action' element (dict)", {}

            status, message, data = execute(action["Action"],
                                            action.get("Parameters", {}))
        else:
            status = "FAILED"
            message = "Encountered unknown structure for Action"
            data = {}

        return status, message, data

    action = action.split(".")

    if len(action) != 2:
        return "FAILED", "Invalid boto3 call: {}".format(".".join(action)), {}

    client, function = action[0], action[1]

    try:
        client = boto3.client(client.lower())
    except Exception as e:
        return "FAILED", "boto3 error: {}".format(e), {}

    try:
        function = getattr(client, function)
    except Exception as e:
        return "FAILED", "boto3 error: {}".format(e), {}

    try:
        response = function(**properties)
    except Exception as e:
        return "FAILED", "boto3 error: {}".format(e), {}

    return "SUCCESS", "Completed successfully", response


def handler(event, context):
    print("Received request:\n", json.dumps(event))

    request = event["RequestType"]
    properties = event["ResourceProperties"]

    if "Actions" not in properties:
        print("Bad properties", properties)
        return sendResponse(event, context, "FAILED",
                            "Missing required parameters")

    if not isinstance(properties["Actions"], dict):
        print("Malformed properties", properties)
        return sendResponse(event, context, "FAILED",
                            "Malformed parameters")

    if request in properties["Actions"]:
        status, message, data = execute(properties["Actions"][request])
        print(f'Execution result:\nstatus = {status}\nmessage = {message}')
        try:
            print(json.dumps(data))
        except Exception:
            print('Could not serialize data structure to JSON')

        result_filter = ""
        if isinstance(properties["Actions"][request], dict):
            result_filter = properties["Actions"][request].get("Filter", "")
        elif (isinstance(properties["Actions"][request], list) and
              isinstance(properties["Actions"][request][-1], dict)):
            result_filter = properties["Actions"][request][-1].get("Filter",
                                                                   "")

        if result_filter:
            try:
                import pyjq
                print(f'Filtering results with "{result_filter}"')
                data = pyjq.first(result_filter, data)
                print("Data after filtering:\n", json.dumps(data))
            except Exception as e:
                return sendResponse(event, context, "FAILED",
                                    "boto3 error: {}".format(e))
        return sendResponse(event, context, status, message, data)

    return sendResponse(event, context, "SUCCESS", "No action taken")
