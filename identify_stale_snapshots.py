#Maximizing AWS Cost Efficiency: Uncovering Stale Snapshots for Optimal Management

#STEP TO PROCESS: https://medium.com/@shashwatkamboj12/automated-cost-optimization-for-aws-snapshots-24bc803df1a1

import boto3

def lambda_handler(event, context):
    ec2 = boto3.client('ec2')
    deleted_snapshots = []

    # Get all EBS snapshots
    response = ec2.describe_snapshots(OwnerIds=['self'])

    # Iterate through each snapshot and delete if it's not attached to any volume or the volume is not attached to a running instance
    for snapshot in response['Snapshots']:
        snapshot_id = snapshot['SnapshotId']
        volume_id = snapshot.get('VolumeId')

        if not volume_id:
            # Delete the snapshot if it's not attached to any volume
            try:
                ec2.delete_snapshot(SnapshotId=snapshot_id)
                deleted_snapshots.append(f"Deleted EBS snapshot {snapshot_id} as it was not attached to any volume.")
            except ec2.exceptions.ClientError as e:
                print(f"Failed to delete snapshot {snapshot_id}: {e}")
        else:
            # Check if the volume still exists
            try:
                volume_response = ec2.describe_volumes(VolumeIds=[volume_id])
                if not volume_response['Volumes'][0]['Attachments']:
                    try:
                        ec2.delete_snapshot(SnapshotId=snapshot_id)
                        deleted_snapshots.append(f"Deleted EBS snapshot {snapshot_id} as it was taken from a volume not attached to any running instance.")
                    except ec2.exceptions.ClientError as e:
                        print(f"Failed to delete snapshot {snapshot_id}: {e}")
            except ec2.exceptions.ClientError as e:
                if e.response['Error']['Code'] == 'InvalidVolume.NotFound':
                    # The volume associated with the snapshot is not found (it might have been deleted)
                    try:
                        ec2.delete_snapshot(SnapshotId=snapshot_id)
                        deleted_snapshots.append(f"Deleted EBS snapshot {snapshot_id} as its associated volume was not found.")
                    except ec2.exceptions.ClientError as e:
                        print(f"Failed to delete snapshot {snapshot_id}: {e}")
    
    # Print all deleted snapshot messages at once for better Lambda logging visibility
    for message in deleted_snapshots:
        print(message)
    
    # Optionally, you can return a summary or success message if needed
    return {
        'statusCode': 200,
        'body': f'{len(deleted_snapshots)} snapshots deleted.'
    }

#You can also automate or Schedule the Deletion of Snapshots with the Help of Amazon EventBridge
