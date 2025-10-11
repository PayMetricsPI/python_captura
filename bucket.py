import logging
import boto3
from botocore.exceptions import ClientError
import os

def upload_file(file_name, bucket, object_name=None):
    if object_name is None:
        object_name = os.path.basename(file_name)

    s3_client = boto3.client('s3')
    try:
        s3_client.upload_file(file_name, bucket, object_name)
    except ClientError as e:
        print("NÃO ESQUEÇA DE ATIVAR O AWS CLI COM SUAS CREDENCIAIS - AWS CONFIGURE")
        logging.error(e)
        return False
    return True