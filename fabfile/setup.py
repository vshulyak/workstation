"""
1. anaconda
2. cuda
3. s3 notebooks, all configs on s3
4. ssh tunnel to main machine for jupyter access (forward logs also?).

5. create ami
6. switch instance types
"""
import time
from fabric.api import env, execute, put, run, settings, hide
from fabric.colors import green, red, yellow
from fabric.operations import sudo
import boto3

"""
Accidentely found this https://github.com/mnielsen/ec2_tools


docker save <docker image name> | gzip > <docker image name>.tar.gz
zcat <docker image name>.tar.gz | docker load


For uploading a stream from stdin to s3, use:
aws s3 cp - s3://my-bucket/stream

For downloading an s3 object as a stdout stream, use:
aws s3 cp s3://my-bucket/stream -

aws s3 cp s3://vshulyak-datasets/workstation_image.tar.gz - | docker load



docker save vshulyak/workstation | gzip > workstation_image.tar.gz
aws s3 cp workstation_image.tar.gz s3://vshulyak-datasets/


ssh -fN -o ExitOnForwardFailure=yes  -L 8888:localhost:8888 ubuntu@35.174.11.163

http://wiki.fast.ai/index.php/AWS_Spot_instances
"""

INSTANCE_NAME = 'vs-workstation'
INSTANCE_TYPES = {
    'small': 't2.medium',
    'medium': 't2.large',
    'gpu': 'p2.xlarge',
    'mem': 'r4.2xlarge',
}
AMI = 'ami-10ef8d6a'
KEYNAME = 'volodja'

env.user = 'ubuntu'
env.connection_attempts = 5
env.timeout = 20
env.keepalive = 10


def setup(type_):
    assert type_ in INSTANCE_TYPES.keys(), "Argument should be in {}".format(", ".join(INSTANCE_TYPES.keys()))
    instance_type = INSTANCE_TYPES[type_]

    instance = get_instance(state='running')

    if not instance:
        print(red("Instance is not running, launching..." % env))
        instance = execute(_setup_instance, ami=AMI, instance_type=instance_type, keyname=KEYNAME)

    instance = get_instance(state='running')
    print(green("Got instance" % env))
    execute(_install_env, instance=instance, hosts=[instance.public_ip_address])


def stop(stop=False):
    """
    ./bin/fab stop_instance:i-0de3c0c5d7fdd2b8b
    """
    instance = get_instance(state='running')
    # stopping one-shot spot instance is forbidden
    if stop:
        instance.stop()
        instance.wait_until_stopped()
    instance.terminate()
    instance.wait_until_terminated()


def _setup_instance(ami, instance_type, keyname):

    ec2 = boto3.resource('ec2')
    instances = ec2.create_instances(
        ImageId=ami,
        InstanceType=instance_type,
        KeyName=keyname,
        BlockDeviceMappings=[
            {
                'DeviceName': '/dev/sda1',
                'Ebs': {
                    'DeleteOnTermination': True,
                    'VolumeSize': 50,
                    'VolumeType': 'gp2'
                }
            },
        ],
        NetworkInterfaces=[
            {
                'DeviceIndex': 0,
                'SubnetId': 'subnet-1d987440',
                'AssociatePublicIpAddress': True,
                'Groups': ['sg-0cf5a27e']
            },
        ],
        TagSpecifications=[
            {
                'ResourceType': 'instance',
                'Tags': [
                    {'Key': 'Name', 'Value': INSTANCE_NAME},
                    {'Key': 'Deploy-Type', 'Value': "throwaway"}
                ]
            },
        ],
        IamInstanceProfile={
            'Name': 'EMR_EC2_DefaultRole',
        },
        InstanceMarketOptions={
            'MarketType': 'spot',
            'SpotOptions': {
                # 'MaxPrice': 'string',
                'SpotInstanceType': 'one-time',  # |'persistent'
                # 'InstanceInterruptionBehavior': 'stop'  # |'terminate' 'hibernate'
            }
        },
        InstanceInitiatedShutdownBehavior='terminate',
        MinCount=1,
        MaxCount=1)

    assert len(instances) == 1, "Got wrong number of instances {}".format(len(instances))
    instance = instances[0]

    print("Created ")
    print("Waiting till it's running...")
    instance.wait_until_running()
    print("Instance {} at {}".format(instance.id, instance.public_ip_address))

    return instance


def get_instance(state=None):
    """
    Gets workstation instance
    """
    ec2 = boto3.resource('ec2')
    filters = [{'Name': 'tag:Name', 'Values': [INSTANCE_NAME]}]
    if state:
        filters.append({'Name': 'instance-state-name', 'Values': [state]})

    try:
        return ec2.instances.filter(Filters=filters).__iter__().next()
    except StopIteration:
        return None


def prices(az='us-east-1a', instance_type=None):
    """
    Get current prices for EC instances of our interest
    """
    client = boto3.client('ec2', region_name='us-east-1')

    if instance_type:
        instance_types = [instance_type]
    else:
        instance_types = INSTANCE_TYPES.values()

    for instance_type in instance_types:
        prices = client.describe_spot_price_history(InstanceTypes=[instance_type],
                                                    MaxResults=1,
                                                    ProductDescriptions=['Linux/UNIX (Amazon VPC)'],
                                                    AvailabilityZone='us-east-1a')
        price_listing = prices['SpotPriceHistory'][0]
        print(price_listing['AvailabilityZone'], price_listing['InstanceType'], price_listing['SpotPrice'])


def _install_env(instance):
    sudo("curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -")
    sudo("curl -s -L https://nvidia.github.io/nvidia-docker/ubuntu16.04/amd64/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list")
    sudo("curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add - ")
    sudo("systemctl stop apt-daily.service")  # disable run when system boot
    sudo("systemctl stop apt-daily.timer")  # disable run when system boot
    sudo("systemctl disable apt-daily.service")  # disable run when system boot
    sudo("systemctl disable apt-daily.timer")  # disable timer run

    # wait till update lock gets released (return_code == 1)
    with hide('output', 'running', 'warnings'), settings(warn_only=True):
        while sudo("lsof /var/lib/dpkg/lock").return_code == 0:
            print(yellow("Sleeping while /var/lib/dpkg/lock is not released" % env))
            time.sleep(5)

    sudo('add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"')
    sudo("apt-get update -y")
    sudo("apt-get install -y docker-ce=18.06.1~ce~3-0~ubuntu nvidia-docker2")
    sudo("usermod -a -G docker ubuntu")
    sudo("pkill -SIGHUP dockerd")
    sudo("pip install --upgrade docker-compose==1.22.0")
    run("mkdir -p ~/project")
    run("mkdir -p ~/project/docker")
    run("mkdir -p ~/project/docker/conf")
    put("docker/conf/.env.env", "~/project/docker/conf/.env.env")
    put("docker-commons.yml", "~/project/docker-commons.yml")

    # copy either CPU or GPU version
    with hide('output', 'running', 'warnings'), settings(warn_only=True):
        if sudo("nvidia-smi").return_code == 0:
            put("docker-compose-gpu.yml", "~/project/docker-compose.yml")
        else:
            put("docker-compose.yml", "~/project/docker-compose.yml")

    # run("docker pull vshulyak/workstation")
    # run("nvidia-docker run --rm vshulyak/workstation")
    print(green("Done pulling" % env))
