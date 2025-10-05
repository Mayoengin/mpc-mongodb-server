"""
Created on 16-apr.-2015

@author: jhuybens
"""

from datetime import timedelta

from normcore.settings import (mongo_db_config_for, mongo_db_test_config_for)
from normprov.settings import NETWORK_ELEMENT_FOR_TEST
from normprov.settings import BFN_ROUTER_FOR_TEST
from normprov.settings import BFN_ROUTER_FOR_TEST_VOGON
from normprov.settings import EDU_FOR_TEST
from normprov.settings import OPENCABLE_ROUTER_FOR_TEST

ALLOWED_NETWORK_ELEMENTS_PROV = [
    EDU_FOR_TEST,
    NETWORK_ELEMENT_FOR_TEST,
    BFN_ROUTER_FOR_TEST,
    BFN_ROUTER_FOR_TEST_VOGON,
    OPENCABLE_ROUTER_FOR_TEST
]


NAS_MONGO_RO_USER = "norm_ro"
NAS_MONGO_RO_PWD = "OGJQrCDnLgK5"
NAS_MONGO_RW_USER = "norm_rw"
NAS_MONGO_RW_PWD = "VoTAZTE0NIsQ"
NAS_MONGO_ADMIN_USER = "norm_admin"
NAS_MONGO_ADMIN_PWD = "zHKJqC9B6hNJ"
NAS_MONGO_AUTH_SOURCE = 'admin'
NAS_MONGO_REPLICASET = 'int.norm.rs01'

NAS_MONGO_HOST = 'mongodb-norm.int.telenet-ops.be'

NAS_MONGO = "{}/{}?replicaSet={}".format(NAS_MONGO_HOST, NAS_MONGO_AUTH_SOURCE, NAS_MONGO_REPLICASET)
NAS_MONGO_RO_HOST = "mongodb://{}:{}@{}".format(NAS_MONGO_RO_USER, NAS_MONGO_RO_PWD, NAS_MONGO)
NAS_MONGO_RW_HOST = "mongodb://{}:{}@{}".format(NAS_MONGO_RW_USER, NAS_MONGO_RW_PWD, NAS_MONGO)
NAS_MONGO_ADMIN_HOST = "mongodb://{}:{}@{}".format(NAS_MONGO_ADMIN_USER, NAS_MONGO_ADMIN_PWD, NAS_MONGO)

MONGODEVSERVERS = [NAS_MONGO_RW_HOST]


NORM_CORE = {
    'mongodb_connection': {
        'db': 'NORM_CORE_DEV',
        'alias': 'NORM_CORE',
        'host': NAS_MONGO_HOST,
        'username': NAS_MONGO_ADMIN_USER,
        'password': NAS_MONGO_ADMIN_PWD,
        'authentication_source': NAS_MONGO_AUTH_SOURCE,
        'replicaset': NAS_MONGO_REPLICASET
    },
    'mongodb_connection_uri': NAS_MONGO_ADMIN_HOST,
    'dtv_service_rpc_server': 'tcp://127.0.0.1:42042',
    'norm_service_api': 'http://normapi-devel.prd.inet.telenet.be:8123/norm_services',
    'norm_services_api': 'http://normapi-devel.prd.inet.telenet.be:8123/service',
    'norm_service_api_key': 'e6180e4a-0a2e-11e7-8faa-0050568546d8',
    'rabbit_mq_server': 'tns2638.telenet-ops.be',
    'rabbit_mq_event_vhost': 'normevent',
    'rabbit_mq_event_username': 'normevent',
    'rabbit_mq_event_password': 'yEvDQ2BW7RqHR6r,',
    'rabbit_mq_logging_username': 'normlog',
    'rabbit_mq_logging_password': 'earoqkjqjF9A1HW4',
    'mongodb_search': mongo_db_config_for('SERVICE_SEARCH', NAS_MONGO_RW_HOST, 'DEV'),
    'encryption_key': b'\xe6\x00"\x0e\x00\xb6"\xcd\x10\x8a\x91\x98H\x07\xb2\x04<}\x1f3\xb9?\xc8t\xab\xbb\x93\xd0\xd8\xba\xdd_'
}

NORM_INV = {
    'mongodb_connection': {
        'db': 'NORM_INV_DEV',
        'alias': 'NORM_INV',
        'host': NAS_MONGO_HOST,
        'username': NAS_MONGO_ADMIN_USER,
        'password': NAS_MONGO_ADMIN_PWD,
        'authentication_source': NAS_MONGO_AUTH_SOURCE,
        'replicaset': NAS_MONGO_REPLICASET
    },
    'mongodb_connection_uri': NAS_MONGO_ADMIN_HOST,
    'probe': {
        'yeti_interconnect_mapping': {
            'BRIN-100-1609': ('SRINTX01', 'lag-140'),
            'TEBR-GBE-1684': ('SRINTX01', 'lag-140'),
            'TEVO-100-4603': ('SRKEIB01', 'lag-140'),
            'TEVO-GBE-4606': ('SRKEIB01', 'lag-140'),
        },
        'tpid_csv_sources': {
            'redundancy': '/data/norm_csv/redundancy/*',
            'yeti': '/data/norm_csv/VOO_IC_TPID*',
            'cnibo_wba_dedicated': '/data/norm_csv/WBA*',
            'vdsl_sharedvlan': '/data/norm_csv/Dsl_Dedicated_Vlan_Products_20*',
            'legacy_tpids': '/data/norm_csv/LEGACY_EXTID.csv',
        },
        'nwo_rest_api': {
            'credentials': 'bdauwe:tele4u2',
            'base_url': 'http://capella.inet.telenet.be/networkobjects/Resources/Api/api.svc/rest/'
        },
        'ruckus_scg_api': {
            'username': 'Telenet-API',
            'password': '^5R7RhGAzcWrJJud',
            'port': '7443',
            'api_version': 'v4_0'
        },
        'ruckus_vsz_api': {
            'username': 'Telenet-API',
            'password': '_"84@8/K!,:JeHcKS}',
            'port': '8443',
            'api_version': 'v8_2'
        },
        'nuage_vspk_api': {
            'nuage_host': '10.45.121.49',
            'nuage_port': '8443',
            'nuage_username': 'ipopsapi',
            'nuage_password': 'SNuhIVzitj',
            'nuage_enterprise': 'csp',
        },
        'nas_ap_discovery_api': {
            'url': 'http://core-tools.prd.inet.telenet.be/publicwifi/sys/ipops/apdiscovery'
        },
        'dtv_dcm_discovery_api': {
            'url': 'http://bennifer.inet.telenet.be:8080/v1/discovery'
        },
        'dtv_services_static': {
            'url': 'https://gaaibaai.inet.telenet.be',
            'xml_file_path': 'cas_drm/static/casis_stby.xml',
        },
        'dtv_tag_discovery_api': {
            'username': 'Admin',
            'password': 'Admin'
        },
        'benu_api': {
            'url': 'http://vcpereport-vip.uat.telenet-ops.be:80/apinorm/'
        },
        'salesforce': {
            'certificate': 'certificates/salesforce_uat_certificate.cer',
            'key': 'certificates/salesforce_uat_key.key',
            'base_url': 'https://sisuat.telenet.be:8021'
        }
    },

}

NORM_RESTAPI = {
    'url': 'http://normapi-devel.prd.inet.telenet.be:8123',
    'mongodb_connection': {
        'db': 'NORM_RESTAPI_DEV',
        'alias': 'NORM_RESTAPI',
        'host': NAS_MONGO_HOST,
        'username': NAS_MONGO_ADMIN_USER,
        'password': NAS_MONGO_ADMIN_PWD,
        'authentication_source': NAS_MONGO_AUTH_SOURCE,
        'replicaset': NAS_MONGO_REPLICASET
    },
    'mongodb_connection_uri': NAS_MONGO_ADMIN_HOST,
}

NORM_DEVICE = {
    'mongodb_test': mongo_db_test_config_for('DEVICE', MONGODEVSERVERS, 'TST'),
    'mongodb_connection': {
        'db': 'NORM_DEVICE_DEV',
        'alias': 'NORM_DEVICE',
        'host': NAS_MONGO_HOST,
        'username': NAS_MONGO_ADMIN_USER,
        'password': NAS_MONGO_ADMIN_PWD,
        'authentication_source': NAS_MONGO_AUTH_SOURCE,
        'replicaset': NAS_MONGO_REPLICASET
    },
    'mongodb_connection_uri': NAS_MONGO_ADMIN_HOST,
    'regex': {
        'DNS': '^(([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9])\.)*([A-Za-z0-9]|[A-Za-z0-9][A-Za-z0-9\-]*[A-Za-z0-9])$',
        'EDU': '^[A-Z0-9]{6}[0-9A-F](S06|V20|S12|S40|S66|V08|V8M)[A-Z0-9]{6}$',
        'EDU_OS906': '^[A-Z0-9]{6}[0-9A-F]S06[A-Z0-9]{6}$',
        'EDU_OS912': '^[A-Z0-9]{6}[0-9A-F]S12[A-Z0-9]{6}$',
        'EDU_OS940': '^[A-Z0-9]{6}[0-9A-F]S40[A-Z0-9]{6}$',
        'EDU_OSV20': '^[A-Z0-9]{6}[0-9A-F]V20[A-Z0-9]{6}$',
        'EDU_OSV8': '^[A-Z0-9]{6}[0-9A-F]V08[A-Z0-9]{6}$',
        'EDU_OSV8M': '^[A-Z0-9]{6}[0-9A-F]V8M[A-Z0-9]{6}$'
    }
}

NORM_PROV = {
    'mongodb_connection': {
        'db': 'NORM_PROV_DEV',
        'alias': 'NORM_PROV',
        'host': NAS_MONGO_HOST,
        'username': NAS_MONGO_ADMIN_USER,
        'password': NAS_MONGO_ADMIN_PWD,
        'authentication_source': NAS_MONGO_AUTH_SOURCE,
        'replicaset': NAS_MONGO_REPLICASET
    },
    'mongodb_connection_uri': NAS_MONGO_ADMIN_HOST,
    'allowed_network_elements': ALLOWED_NETWORK_ELEMENTS_PROV,
    'asap': {
        'default_env': "DVP",
        'timeout': 3,
    },
    'pgw': {
        'ip_address': 'voice-provgw.int.telenet-ops.be',  # '192.168.180.129',
        'port': 80,
        'restapi': {
            'username': 'admin',  # "pgwadmin",
            'password': 'admin',  # "telenet",
        }
    },
    'link': {
        'network_connector_class_fqn': 'normprov.tasks.common.connectors.linkconnector.LinkConnectorForTest'
    },
    'templates': {
        # FIXME this doesn't seem used anymore (cf. normprov.settings)
        'basedir': "/ipops/prod/norm/norm_network_templates"
    },
    'fip_bfn': {
        'router_tags': ['NORM', 'DC', 'MX', 'JUNOS', 'NAGIOS_EXCLUDE', 'LABO'],
        'mail_addresses_notifications': [],
        'secs_between_retries_static_route_provisioning': 300,
        'nr_retries_static_route_provisioning': 5,
    },
    'dsl': {
        'nr_days_in_flatfile_before_deprovision': 3,
        'max_nr_saps_to_deprovision': 20,
    },
    'apn': {
        'isps': {
            'url': 'http://norm.ws.isps.rest.uat.telenet-ops.be:1420/ipaccess/mobilesubscriberb2bs',
            'username': 'NORM_UAT',
            'password': '5GEfe4fPpmM6Rkn3',
            'roles': ['ROLE_IPACCESS']
        },
    },
    'vdsl': {
        'isps': {
            'url': 'http://isps.uat.telenet-ops.be:7010/wscli/wscli-ipops.cgi',
        },
    },
    'apio': {
        'host': 'apio.centrex.int.telenet-ops.be',
        'token': '3fa34410689ac9f3289627fd69b0de867104becd',
    },
    "fsps": {
        "credentials": {
            "INT": {
                "user": "NORM_INT",
                "password": "c8TkXJvfyQN7pR2u",
            },
            "STG": {
                "user": "NORM_STG",
                "password": "rDZ6vSEupG87CjMg",
            },
        },
    },
}


NORM_TASK = {
    'mongodb_connection': {
        'db': 'NORM_TASK_DEV',
        'alias': 'NORM_TASK',
        'host': NAS_MONGO_HOST,
        'username': NAS_MONGO_ADMIN_USER,
        'password': NAS_MONGO_ADMIN_PWD,
        'authentication_source': NAS_MONGO_AUTH_SOURCE,
        'replicaset': NAS_MONGO_REPLICASET
    },
    'mongodb_connection_uri': NAS_MONGO_ADMIN_HOST,
    'tasks_retry_timer_in_secs': 60,
    'broker_url': 'amqp://normtask:VOQQl8b87jO.pzoJ@tns2638.telenet-ops.be/normtask',
    'celery_result_backend': 'mongodb',
    'celery_mongodb_backend_settings': {
        'taskmeta_collection': 'task_meta',
        'database': 'NORM_CELERY_DEV',
        'host': MONGODEVSERVERS
    },
    'celerybeat_schedule': {
        'check-orders-every-minute-ftth': {
            'task': 'normtask.tasks.tasks.check_workorders',
            'schedule': timedelta(seconds=300),
            'args': ("check-orders-every-day",
                     "normprov.tasks.ccap.models.ccapworkorder.FtthWorkOrder",
                     "normprov.tasks.ccap.tasks.WorkflowMatcherFtth",
                     ),
        },
        'check-orders-every-minute': {
            'task': 'normtask.tasks.tasks.check_workorders',
            'schedule': timedelta(seconds=300),
            'args': ("check-orders-every-day", "normprov.tasks.ccap.models.ccapworkorder.Ccap2WorkOrder",
                     "normprov.tasks.ccap.tasks.WorkflowMatcherCcap2"),
        },
        'check-swap-orders-every-minute-sapswap': {
            'task': 'normtask.tasks.tasks.check_workorders',
            'schedule': timedelta(seconds=300),
            'args': ("every-5-minutes", "normprov.tasks.ccap.models.ccapworkorder.SapSwap2Order",
                     "normprov.tasks.ccap.tasks.WorkflowMatcherCcap2"),
        },
        'cleanup_metas': {
            'task': 'normtask.tasks.tasks.cleanup_task_metas',
            'schedule': timedelta(seconds=300),
            'args': (),
        },
    },
    'celerybeat_schedule_filename': '/data/norm/celerytask/celerybeat-schedule'
}

NORM_IPAM = {
    'mongodb_connection': {
        'db': 'NORM_IPAM_DEV',
        'alias': 'NORM_IPAM',
        'host': NAS_MONGO_HOST,
        'username': NAS_MONGO_ADMIN_USER,
        'password': NAS_MONGO_ADMIN_PWD,
        'authentication_source': NAS_MONGO_AUTH_SOURCE,
        'replicaset': NAS_MONGO_REPLICASET
    },
    'mongodb_connection_uri': NAS_MONGO_ADMIN_HOST,
    'nw_types_for_ip_subnets_report': ["CUST_FIBRE_LAN", "CUST_FIBRE_WAN"],
    'ants': {
        'host': 'antsapi.vtp.inet.telenet.be',
        'username': 'ipops',
        'password': 'AzBW8PgfmrwXg8K8',
        'allowed_ccaps': ['CAP17TEST03'],
        'allowed_subnets': ['81.82.75.0/24']
    },
}

NORM_RESMAN = {
    'mongodb_connection': {
        'db': 'NORM_RESMAN_DEV',
        'alias': 'NORM_RESMAN',
        'host': NAS_MONGO_HOST,
        'username': NAS_MONGO_ADMIN_USER,
        'password': NAS_MONGO_ADMIN_PWD,
        'authentication_source': NAS_MONGO_AUTH_SOURCE,
        'replicaset': NAS_MONGO_REPLICASET
    },
    'mongodb_connection_uri': NAS_MONGO_ADMIN_HOST,
    'vlan_notifications': {
        'subscribers': []
    }
}

NORM_VIEW = {
    'dtv_failed_discoveries_report': {
        'recipients': []
    }
}

NORM = {
    'NORM_CORE': NORM_CORE,
    'NORM_INV': NORM_INV,
    'NORM_RESTAPI': NORM_RESTAPI,
    'NORM_DEVICE': NORM_DEVICE,
    'NORM_PROV': NORM_PROV,
    'NORM_TASK': NORM_TASK,
    'NORM_IPAM': NORM_IPAM,
    'NORM_RESMAN': NORM_RESMAN,
    'NORM_VIEW': NORM_VIEW,
}

LOGGING = {'loggers':
           {'':
            {
                'level': 'DEBUG'}
            }
           }
