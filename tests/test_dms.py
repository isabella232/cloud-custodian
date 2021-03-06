# Copyright 2017 Capital One Services, LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from .common import BaseTest


class ReplInstance(BaseTest):
    def test_describe_augment_no_tags(self):
        session_factory = self.replay_flight_data(
            'test_dms_repl_instance_describe_sans_tags')
        p = self.load_policy({
            'name': 'dms-replinstance',
            'resource': 'dms-instance'},
            session_factory=session_factory)        
        resources = p.run()
        self.assertEqual(len(resources), 1)
        self.assertEqual(resources[0]['ReplicationInstanceIdentifier'],
                         'replication-instance-1')

    def test_describe_get_resources(self):
        session_factory = self.replay_flight_data(
            'test_dms_repl_instance_delete')
        p = self.load_policy({
            'name': 'dms-replinstance',
            'resource': 'dms-instance'},
            session_factory=session_factory)        
        resources = p.resource_manager.get_resources(
            ['replication-instance-1'])
        self.assertEqual(len(resources), 1)
        self.assertEqual(resources[0]['ReplicationInstanceIdentifier'],
                         'replication-instance-1')        

    def test_delete(self):
        session_factory = self.replay_flight_data(
            'test_dms_repl_instance_delete')
        client = session_factory().client('dms')
        p = self.load_policy({
            'name': 'dms-replinstance',
            'resource': 'dms-instance',
            'actions': ['delete']},
            session_factory=session_factory)        
        resources = p.run()
        self.assertEqual(len(resources), 1)
        self.assertEqual(resources[0]['ReplicationInstanceIdentifier'],
                         'replication-instance-1')
        instances = client.describe_replication_instances().get(
            'ReplicationInstances')
        self.assertEqual(instances[0]['ReplicationInstanceStatus'], 'deleting')


class ReplicationInstanceTagging(BaseTest):
    def test_replication_instance_tag(self):
        session_factory = self.replay_flight_data('test_dms_tag')
        p = self.load_policy({
            'name': 'tag-dms-instance',
            'resource': 'dms-instance',
            'filters': [{
                'tag:RequiredTag': 'absent'}],
            'actions': [{
                'type': 'tag',
                'key': 'RequiredTag',
                'value': 'RequiredValue'
            }]
        }, session_factory=session_factory)
        resources = p.run()
        self.assertEqual(len(resources), 1)
        client = session_factory(region='us-east-1').client('dms')
        tag_list = client.list_tags_for_resource(
            ResourceArn=resources[0]['ReplicationInstanceArn'])['TagList']
        tag_value = [t['Value'] for t in tag_list if t['Key'] == 'RequiredTag']
        self.assertEqual(tag_value[0], 'RequiredValue')

    def test_remove_replication_instance_tag(self):
        session_factory = self.replay_flight_data('test_dms_tag_remove')
        p = self.load_policy({
            'name': 'remove-dms-tag',
            'resource': 'dms-instance',
            'filters': [{
                'tag:RequiredTag': 'RequiredValue'}],
            'actions': [{
                'type': 'remove-tag',
                'tags': ["RequiredTag"]
            }]}, session_factory=session_factory)
        resources = p.run()
        self.assertEqual(len(resources), 1)
        client = session_factory(region='us-east-1').client('dms')
        tag_list = client.list_tags_for_resource(
           ResourceArn=resources[0]['ReplicationInstanceArn'])['TagList']
        self.assertFalse([t for t in tag_list if t['Key'] == 'RequiredTag'])

    def test_replication_instance_markforop(self):
        session_factory = self.replay_flight_data('test_dms_mark_for_op')
        p = self.load_policy({
            'name': 'dms-instance-markforop',
            'resource': 'dms-instance',
            'filters': [{
                'tag:RequiredTag': 'absent'}],
            'actions': [{
                'type': 'mark-for-op',
                'tag': 'custodian_cleanup',
                'op': 'delete',
                'days': 2}]}, session_factory=session_factory)
        resources = p.run()
        self.assertEqual(len(resources), 1)
        client = session_factory(region='us-east-1').client('dms')
        tag_list = client.list_tags_for_resource(
            ResourceArn=resources[0]['ReplicationInstanceArn'])['TagList']
        self.assertTrue(
            [t['Value'] for t in tag_list if t['Key'] == 'custodian_cleanup'])

    def test_replication_instance_markedforop(self):
        session_factory = self.replay_flight_data('test_dms_marked_for_op')
        p = self.load_policy({
            'name': 'dms-instance-markedforop',
            'resource': 'dms-instance',
            'filters': [{
                'type': 'marked-for-op',
                'tag': 'custodian_cleanup',
                'op': 'delete',
                'skew': 2}]}, session_factory=session_factory)
        resources = p.run()
        self.assertEqual(len(resources), 1)
        self.assertEqual(
            resources[0]['ReplicationInstanceIdentifier'],
            'replication-instance-1')


class DmsEndpointTests(BaseTest):

    def test_resource_query(self):
        session_factory = self.replay_flight_data('test_dms_resource_query')
        p = self.load_policy({
            'name': 'dms-endpoint-query',
            'resource': 'dms-endpoint'}, session_factory=session_factory)
        resources = p.run()
        self.assertEqual(len(resources), 1)

    def test_endpoint_modify_sql(self):
        session_factory = self.replay_flight_data(
            'test_dms_modify_endpoint_sql')
        p = self.load_policy({
            'name': 'dms-sql-ssl',
            'resource': 'dms-endpoint',
            'filters': [
                {'EndpointIdentifier': 'c7n-dms-sql-ep'},
                {'ServerName': 'c7n-sql-db'}
            ],
            'actions': [{
                'type': 'modify-endpoint',
                'Port': 3305,
                'SslMode': 'require',
                'Username': 'admin',
                'Password': 'sqlpassword',
                'ServerName': 'c7n-sql-db-02',
                'DatabaseName': 'c7n-db-02',
            }]}, session_factory=session_factory)
        resources = p.run()
        self.assertEqual(len(resources), 1)
        client = session_factory(region='us-east-1').client('dms')
        ep = client.describe_endpoints()['Endpoints'][0]
        self.assertEqual(
            [ep['Port'], ep['SslMode'], ep['Username'],
             ep['ServerName'], ep['DatabaseName']],
            [3305, 'require', 'admin', 'c7n-sql-db-02', 'c7n-db-02'])

    def test_endpoint_modify_s3(self):
        session_factory = self.replay_flight_data(
            'test_dms_modify_endpoint_s3')
        p = self.load_policy({
            'name': 'dms-s3-bucket',
            'resource': 'dms-endpoint',
            'filters': [
                {'EndpointIdentifier': 'c7n-dms-s3-ep'},
                {'S3Settings.BucketFolder': 'absent'}
            ],
            'actions': [{
                'type': 'modify-endpoint',
                'S3Settings': {
                    'BucketFolder': 's3_dms',
                    'ServiceAccessRoleArn': 'arn:aws:iam::644160558196:role/DMS-Test-Role-02',
                    'CompressionType': 'gzip'}}]},
            session_factory=session_factory)
        resources = p.run()
        self.assertEqual(len(resources), 1)
        client = session_factory(region='us-east-1').client('dms')
        ep = client.describe_endpoints()['Endpoints'][0]
        self.assertEqual([
            ep['S3Settings']['ServiceAccessRoleArn'],
            ep['S3Settings']['CompressionType'],
            ep['S3Settings']['BucketFolder']],
            ['arn:aws:iam::644160558196:role/DMS-Test-Role-02', 'GZIP',
             's3_dms'])

    def test_endpoint_modify_mongodb(self):
        session_factory = self.replay_flight_data(
            'test_dms_modify_endpoint_mongodb')
        p = self.load_policy({
            'name': 'dms-mongo-db',
            'resource': 'dms-endpoint',
            'filters': [{'EndpointIdentifier': 'c7n-dms-mongo-ep'}],
            'actions': [{
                'type': 'modify-endpoint',
                'MongoDbSettings': {
                    'Username': 'madmin',
                    'Password': 'mongopassword',
                    'ServerName': 'c7n-mongo-db-02',
                    'NestingLevel': 'one',
                    'AuthSource': 'c7n-users-02'}}]},
            session_factory=session_factory)
        resources = p.run()
        self.assertEqual(len(resources), 1)
        client = session_factory(region='us-east-1').client('dms')
        ep = client.describe_endpoints()['Endpoints'][0]['MongoDbSettings']
        self.assertEqual([
            ep['Username'], ep['ServerName'],
            ep['NestingLevel'], ep['AuthSource']],
            ['madmin', 'c7n-mongo-db-02', 'one', 'c7n-users-02'])

    def test_endpoint_modify_dynamo(self):
        session_factory = self.replay_flight_data(
            'test_dms_modify_endpoint_dynamo')
        p = self.load_policy({
            'name': 'dms-mongo-db',
            'resource': 'dms-endpoint',
            'filters': [
                {'EndpointIdentifier': 'c7n-dms-dynamo-ep'},
                {'DynamoDbSettings.ServiceAccessRoleArn': 'arn:aws:iam::644160558196:role/DMS-Test-Role-01'}
            ],
            'actions': [{
                'type': 'modify-endpoint',
                'DynamoDbSettings': {
                    'ServiceAccessRoleArn': 'arn:aws:iam::644160558196:role/DMS-Test-Role-02'
                }}]},session_factory=session_factory)
        resources = p.run()
        self.assertEqual(len(resources), 1)
        client = session_factory(region='us-east-1').client('dms')
        ep = client.describe_endpoints()['Endpoints'][0]['DynamoDbSettings']
        self.assertEqual(ep['ServiceAccessRoleArn'],
                         'arn:aws:iam::644160558196:role/DMS-Test-Role-02')
