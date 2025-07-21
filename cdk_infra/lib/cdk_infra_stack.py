from aws_cdk import (
    Stack,
    aws_lambda as lambda_,
    aws_rds as rds,
    aws_ec2 as ec2,
    aws_apigateway as apigw,
    aws_iam as iam,
    Duration,
    RemovalPolicy,
    CfnOutput
)
from constructs import Construct

class CdkInfraStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # 1. VPCの作成 (既存のVPCを利用することも可能)
        # コスト削減のため、NAT GatewayなしのVPCを作成
        vpc = ec2.Vpc(self, "AppVpc",
            max_azs=2,
            nat_gateways=0,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="Public",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24
                ),
                ec2.SubnetConfiguration(
                    name="Private",
                    subnet_type=ec2.SubnetType.PRIVATE_ISOLATED,
                    cidr_mask=24
                )
            ]
        )

        # 2. RDS PostgreSQLデータベースの作成
        # DB接続情報はSecrets Managerに自動生成される
        db_instance = rds.DatabaseInstance(self, "ReleaseNoteDB",
            engine=rds.DatabaseInstanceEngine.postgres(
                version=rds.PostgresEngineVersion.VER_15
            ),
            instance_type=ec2.InstanceType.of(
                ec2.InstanceClass.BURSTABLE3, ec2.InstanceSize.MICRO
            ),
            vpc=vpc,
            database_name="doc_sage_db",
            credentials=rds.Credentials.from_generated_secret("dbadmin"),
            multi_az=False,
            allocated_storage=20,
            publicly_accessible=False,
            removal_policy=RemovalPolicy.DESTROY # 開発用: スタック削除時にDBも削除 (本番では変更)
        )

        # 3. Lambda関数のIAMロール
        lambda_role = iam.Role(self, "LambdaExecutionRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaVPCAccessExecutionRole"),
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole") # CloudWatch Logsへの書き込み
            ]
        )
        # Bedrockへのアクセス権限を追加
        lambda_role.add_to_policy(iam.PolicyStatement(
            actions=["bedrock:InvokeModel", "bedrock:ListFoundationModels"],
            resources=["*"] # 特定のモデルに絞ることも可能
        ))
        # RDSの認証情報へのアクセス権限を追加
        lambda_role.add_to_policy(iam.PolicyStatement(
            actions=["secretsmanager:GetSecretValue"],
            resources=[db_instance.secret.secret_arn]
        ))

        # 4. Lambda関数の作成
        # コードは後で配置する 'lambda_code' ディレクトリから読み込む
        release_note_lambda = lambda_.Function(self, "ReleaseNoteGenerator",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="main_logic.generate_release_note_draft", # main_logic.pyの関数名
            code=lambda_.Code.from_asset("../lambda_code"), # プロジェクトルートからの相対パス
            memory_size=512,
            timeout=Duration.seconds(60),
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_ISOLATED), # プライベートサブネットに配置
            allow_public_subnet=True, # NAT GatewayがないVPCでインターネットアクセスが必要な場合
            role=lambda_role,
            environment={
                "ENV": "aws",
                "DB_SECRET_ARN": db_instance.secret.secret_arn,
                "AWS_BEDROCK_EMBEDDING_MODEL_ID": "amazon.titan-embed-text-v1",
                "AWS_BEDROCK_LLM_MODEL_ID": "anthropic.claude-3-sonnet-20240229-v1_0",
            }
        )

        # LambdaがRDSに接続できるようにセキュリティグループを設定
        db_instance.connections.allow_from(release_note_lambda, ec2.Port.tcp(5432), "Allow Lambda to connect to RDS")

        # 5. API Gatewayの作成
        api = apigw.LambdaRestApi(self, "ReleaseNoteApi",
            handler=release_note_lambda,
            proxy=True
        )

        # API GatewayのURLを出力
        CfnOutput(self, "ApiUrl", value=api.url)
