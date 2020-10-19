import os

PREFIX = "AWS::Boto"

LAMBDA_ARN = os.environ["LAMBDA_ARN"]

def handle_template(request_id, template):
    for name, resource in template.get("Resources", {}).items():
        if resource["Type"] == PREFIX:
            resource.update({
                "Type": "Custom::Boto3",
                "Version": "1.0",
                "Properties": {
                    "ServiceToken": LAMBDA_ARN,
                    "Actions": resource.get("Actions", {}),
                },
            })

            if "Actions" in resource:
                del resource["Actions"]

    return template

def handler(event, context):
    fragment = event["fragment"]
    status = "success"

    try:
        fragment = handle_template(event["requestId"], event["fragment"])
    except Exception as e:
        status = "failure"

    return {
        "requestId": event["requestId"],
        "status": status,
        "fragment": fragment,
    }
