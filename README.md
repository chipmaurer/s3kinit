# This software is distributed 'as is' and with no warranties of any kind, whether express or implied, including and without limitation, any warranty of merchantability or fitness for a particular purpose.

# The user (you) must assume the entire risk of using the software.

# In no event shall any individual, company or organization involved in any way in the development, sale or distribution of this software be liable for any damages whatsoever relating to the use, misuse, or inability to use this software (including, without limitation, damages for loss of profits, business interruption, loss of information, or any other loss).'

The s3kinit python script is a helper script for Hadoop systems where interactive
users want to authenticate to an ADFS Identity Provider that has a cross realm trust
with an ECS storage cluster (version 3.5 or above).  The s3kinit script then will
show the user which roles on the ECS can be assumed, and the user would then select
one of the possible roles.  The script then sends a SAML assertion request to the 
STS on the ECS, and responds with temporary ECS S3 credentials which the user can
then use in requests to the ECS for secure access to an ECS S3 bucket.

Installation
------------

Copy the s3kinit.py script to any/all Hadoop nodes in the cluster that are required
for interactive users to access ECS S3 storage using IAM policies.

Since most Hadoop clusters run python 2.7, this script is only supported for that
version of python.  Also, this script requires the download of the following
python packages via pip: boto, requests, bs4

Usage
-----

The s3kinit.py script can be run from the command line as follows.  The only argument
is an optional -H argument, which requests the number of hours for the credentials
to be valid for (minimum 1, maximum 12).  The user enters their username on the
Identity Provider (user@domain), then the password, and then the number which 
corresponds to the role they wish to assume.

[chip@lrmk025 ~]$ s3kinit.py -H 12<br/>
Username@Domain:  chip@HDFS.EMC.COM<br/>
Password: <PASSWORD>

Following provider role combination can be used with assertion provided with ECS assumerolewithsaml api<br/>
[ 0 ]:  urn:ecs:iam::s3:role/ADFS-AdminUser urn:ecs:iam::s3:saml-provider/HadoopProvider<br/>
Enter the number for the role to assume (between 0 and 0):  0<br/>
You chose role urn:ecs:iam::s3:role/ADFS-AdminUser and provider urn:ecs:iam::s3:saml-provider/HadoopProvider<br/>

Access Key: ASIA08D38B57E42710C5<br/>
Secret Key: wnFHFMzryQmXZ8x7MsBKIRaMMp-xH7HkEin54HDZLLU<br/>
Session Token: CgJzMxoUQVJPQUMzQTBCOTYwN0JDNzQyOUQiI3VybjplY3M6aWFtOjpzMzpyb2xlL0FERlMtQWRtaW5Vc2VyKhRBU0lBMDhEMzhCNTdFNDI3MTBDNTJQTWFzdGVyS2V5UmVjb3JkLTNkYTRlMmU2YzIwY2IzODY0NWVlMmViOWQ1ZTFjNTE4MmJhMGFiNDc1YjEwODhhYTk0MGYzMjJlMDI1YTNjZDU4rrPatqkuUhFjaGlwQGRldi5udWxsLmNvbVonCghzYW1sOmF1ZBIbaHR0cHM6Ly8xMC4yNDcuMTc5LjExMi9zYW1sWhUKCHNhbWw6c3ViEglIREZTXGNoaXBaGwoNc2FtbDpzdWJfdHlwZRIKcGVyc2lzdGVudFoyChJzYW1sOm5hbWVxdWFsaWZpZXISHHRXK0dxRVVuWVJsZ1A2R00yTFZBQWcrcFUwdz1aNgoIc2FtbDppc3MSKmh0dHA6Ly9BRC5oZGZzLmVtYy5jb20vYWRmcy9zZXJ2aWNlcy90cnVzdGIsdXJuOmVjczppYW06OnMzOnNhbWwtcHJvdmlkZXIvSGFkb29wUHJvdmlkZXJogY359gU
Expiration Date (UTC): 2020-06-09T02:09:05Z

Use these Hadoop settings: -D fs.s3a.secret.key=wnFHFMzryQmXZ8x7MsBKIRaMMp-xH7HkEin54HDZLLU -D fs.s3a.access.key=ASIA08D38B57E42710C5 -D fs.s3a.aws.credentials.provider=org.apache.hadoop.fs.s3a.TemporaryAWSCredentialsProvider -D fs.s3a.session.token=CgJzMxoUQVJPQUMzQTBCOTYwN0JDNzQyOUQiI3VybjplY3M6aWFtOjpzMzpyb2xlL0FERlMtQWRtaW5Vc2VyKhRBU0lBMDhEMzhCNTdFNDI3MTBDNTJQTWFzdGVyS2V5UmVjb3JkLTNkYTRlMmU2YzIwY2IzODY0NWVlMmViOWQ1ZTFjNTE4MmJhMGFiNDc1YjEwODhhYTk0MGYzMjJlMDI1YTNjZDU4rrPatqkuUhFjaGlwQGRldi5udWxsLmNvbVonCghzYW1sOmF1ZBIbaHR0cHM6Ly8xMC4yNDcuMTc5LjExMi9zYW1sWhUKCHNhbWw6c3ViEglIREZTXGNoaXBaGwoNc2FtbDpzdWJfdHlwZRIKcGVyc2lzdGVudFoyChJzYW1sOm5hbWVxdWFsaWZpZXISHHRXK0dxRVVuWVJsZ1A2R00yTFZBQWcrcFUwdz1aNgoIc2FtbDppc3MSKmh0dHA6Ly9BRC5oZGZzLmVtYy5jb20vYWRmcy9zZXJ2aWNlcy90cnVzdGIsdXJuOmVjczppYW06OnMzOnNhbWwtcHJvdmlkZXIvSGFkb29wUHJvdmlkZXJogY359gU






