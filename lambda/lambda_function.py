import boto3
from datetime import datetime, timedelta

CPU_THRESHOLD = 5
TIME_PERIOD = 10
REGION = "ap-south-1"

def lambda_handler(event, context):
    print("Lambda started")

    ec2 = boto3.client('ec2', region_name=REGION)
    cloudwatch = boto3.client('cloudwatch', region_name=REGION)

    instances = ec2.describe_instances()

    for reservation in instances['Reservations']:
        for instance in reservation['Instances']:
            instance_id = instance['InstanceId']
            state = instance['State']['Name']

            print(f"Checking {instance_id}")

            if state != 'running':
                continue

            tags = {tag['Key']: tag['Value'] for tag in instance.get('Tags', [])}

            if tags.get('AutoStop') != 'true':
                continue

            metrics = cloudwatch.get_metric_statistics(
                Namespace='AWS/EC2',
                MetricName='CPUUtilization',
                Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}],
                StartTime=datetime.utcnow() - timedelta(minutes=TIME_PERIOD),
                EndTime=datetime.utcnow(),
                Period=300,
                Statistics=['Average']
            )

            if metrics['Datapoints']:
                datapoints = sorted(metrics['Datapoints'], key=lambda x: x['Timestamp'])
                avg_cpu = datapoints[-1]['Average']

                print(f"{instance_id} CPU: {avg_cpu}")

                if avg_cpu < CPU_THRESHOLD:
                    ec2.stop_instances(InstanceIds=[instance_id])
                    print(f"Stopped {instance_id}")

    return "Done"