# // Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# // SPDX-License-Identifier: MIT-0

from aws_cdk import (
    core,
    aws_cloudfront_origins as origins,
    aws_cloudfront as cf,
    aws_elasticloadbalancingv2 as alb,
    aws_s3 as s3
)

class NestedStack(core.NestedStack):

    @property
    def jhub_cf(self):
        return self._jhub_cf

    @property
    def argo_cf(self):
        return self._argo_cf

    def __init__(self, scope: core.Construct, id: str,logbucket: str,argo_alb_dns_name: str, jhub_alb_dns_name: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

# //**********************************************************************************************************//
# //*************************** Add CloudFront to enable HTTPS Endpoint (OPTIONAL) **************************//
# //***** recommended way is to generate your own SSL certificate via AWS Certificate Manager ***************//
# //****************************** add it to the application load balancer *********************************//
# //*******************************************************************************************************//
        self._bucket=s3.Bucket.from_bucket_name(self,'cf_logbucket', logbucket)
        self._jhub_cf = add_distribution(self, 'jhub_dist', jhub_alb_dns_name, 80, self._bucket)
        self._argo_cf = add_distribution(self, 'argo_dist', argo_alb_dns_name, 2746, self._bucket)


def add_distribution(scope: core.Construct, id: str, alb_dns_name: str, port: int, logbucket: s3.IBucket
) -> cf.IDistribution:

    load_balancer_arn=core.Fn.get_att(alb_dns_name,"DNSName")
    security_group_id=core.Fn.get_att(alb_dns_name,"SecurityGroups")

    alb2 = alb.ApplicationLoadBalancer.from_application_load_balancer_attributes(scope, id,
            load_balancer_arn=load_balancer_arn.to_string(),
            security_group_id=security_group_id.to_string(),
            load_balancer_dns_name=alb_dns_name
        )
    _origin = origins.LoadBalancerV2Origin(alb2,
        http_port=port,
        protocol_policy=cf.OriginProtocolPolicy.HTTP_ONLY
    )
    dist = cf.Distribution(scope, "CF-"+id,
        default_behavior={
            "origin": _origin,
            "allowed_methods": cf.AllowedMethods.ALLOW_ALL,
            "cache_policy": cf.CachePolicy.CACHING_DISABLED,
            "origin_request_policy": cf.OriginRequestPolicy.ALL_VIEWER,
            "viewer_protocol_policy": cf.ViewerProtocolPolicy.REDIRECT_TO_HTTPS
        },
        minimum_protocol_version=cf.SecurityPolicyProtocol.TLS_V1_2_2019,
        enable_logging=True,
        log_bucket=logbucket
    )
    return dist.distribution_domain_name
