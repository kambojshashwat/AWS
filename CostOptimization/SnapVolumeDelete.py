#WITH THIS LAMBDA FUNCTION CODE IT WILL TAKE SNAPSHOT OF VOLUMES WITH THE TAG: NAME: DEV AND THEN DELETE THE VOLUMES - AS SNASPHOT IS CREATED...
#BUT WILL NOT WORK WITH VOLUMES ATTACHED TO EC2 INSTANCES - BUT YOU CAN MODIFY THAT...

import json
import boto3
import logging

# Initialize boto3 clients
ec2_client = boto3.client('ec2')
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    try:
        # Describe volumes with the tag 'Dev'
        volumes = ec2_client.describe_volumes(
            Filters=[
                {
                    'Name': 'tag:Name',
                    'Values': ['Dev']
                }
            ]
        )
        
        for volume in volumes['Volumes']:
            volume_id = volume['VolumeId']
            attachments = volume['Attachments']
            
            if attachments:
                logger.info(f"Volume {volume_id} is attached to an instance, skipping snapshot and deletion")
                continue

            logger.info(f"Processing volume: {volume_id}")
            
            # Create a snapshot of the volume
            snapshot = ec2_client.create_snapshot(VolumeId=volume_id, Description=f"Snapshot of {volume_id}")
            snapshot_id = snapshot['SnapshotId']
            logger.info(f"Created snapshot {snapshot_id} for volume {volume_id}")

            # Wait for the snapshot to be completed
            waiter = ec2_client.get_waiter('snapshot_completed')
            waiter.wait(SnapshotIds=[snapshot_id])
            logger.info(f"Snapshot {snapshot_id} completed")

            # Delete the volume
            ec2_client.delete_volume(VolumeId=volume_id)
            logger.info(f"Deleted volume {volume_id}")
            
    except Exception as e:
        logger.error(f"Error processing volumes: {str(e)}")
        raise

    return {
        'statusCode': 200,
        'body': json.dumps('Snapshots created and volumes deleted successfully for unattached volumes')
    }
