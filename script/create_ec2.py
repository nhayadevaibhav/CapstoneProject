import boto3

ec2 = boto3.resource('ec2', region_name='ap-south-1')

instance = ec2.create_instances(
    ImageId='ami-0f58b397bc5c1f2e8',
    MinCount=1,
    MaxCount=1,
    InstanceType='t3.micro',
    TagSpecifications=[{
        'ResourceType': 'instance',
        'Tags': [
            {'Key': 'AutoStop', 'Value': 'true'}
        ]
    }]
)

print("Created:", instance[0].id)