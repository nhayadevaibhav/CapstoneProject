import boto3
import json
import time

iam = boto3.client('iam')
lambda_client = boto3.client('lambda')
events = boto3.client('events')
sts = boto3.client('sts')

ROLE_NAME = "CostOptimizerRole"
FUNCTION_NAME = "CostOptimizerLambda"

# Create IAM Role
assume_policy = {
    "Version": "2012-10-17",
    "Statement": [{
        "Effect": "Allow",
        "Principal": {"Service": "lambda.amazonaws.com"},
        "Action": "sts:AssumeRole"
    }]
}

try:
    role = iam.create_role(
        RoleName=ROLE_NAME,
        AssumeRolePolicyDocument=json.dumps(assume_policy)
    )
except:
    role = iam.get_role(RoleName=ROLE_NAME)

policies = [
    "arn:aws:iam::aws:policy/AmazonEC2FullAccess",
    "arn:aws:iam::aws:policy/CloudWatchReadOnlyAccess",
    "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
]

for p in policies:
    iam.attach_role_policy(RoleName=ROLE_NAME, PolicyArn=p)

time.sleep(10)

# Create/Update Lambda
with open("../lambda/function.zip", "rb") as f:
    code = f.read()

try:
    lambda_client.create_function(
        FunctionName=FUNCTION_NAME,
        Runtime='python3.9',
        Role=role['Role']['Arn'],
        Handler='lambda_function.lambda_handler',
        Code={'ZipFile': code},
        Timeout=60
    )
    print("Lambda created")
except:
    lambda_client.update_function_code(
        FunctionName=FUNCTION_NAME,
        ZipFile=code
    )
    print("Lambda updated")

# Create schedule
rule = events.put_rule(
    Name="CostOptimizerSchedule",
    ScheduleExpression="rate(10 minutes)",
    State="ENABLED"
)

account_id = sts.get_caller_identity()["Account"]

events.put_targets(
    Rule="CostOptimizerSchedule",
    Targets=[{
        "Id": "1",
        "Arn": f"arn:aws:lambda:ap-south-1:{account_id}:function:{FUNCTION_NAME}"
    }]
)

try:
    lambda_client.add_permission(
        FunctionName=FUNCTION_NAME,
        StatementId="EventBridgeInvoke",
        Action="lambda:InvokeFunction",
        Principal="events.amazonaws.com",
        SourceArn=rule['RuleArn']
    )
except:
    pass

print("Deployment completed")