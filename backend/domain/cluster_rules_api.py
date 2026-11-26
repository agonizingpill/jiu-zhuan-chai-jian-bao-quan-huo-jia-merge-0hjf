from fastapi import APIRouter, Depends

from core.auth import actor, allow
from core.audit import record
from core.db import transaction
from core.records import scan
from domain import cluster_rules_service as service
from domain.cluster_rules_model import cluster_evaluations, cluster_rules
from domain.cluster_rules_schemas import ProposeRule, EvaluateRule, PublishRule

router = APIRouter()

STATES = {'current': '现用', 'pending': '待发布', 'retired': '已停用', 'superseded': '已作废'}


@router.get('/cluster_rules')
def list_cluster_rules(user=Depends(actor)):
    with transaction() as conn:
        rules = sorted(scan(conn, cluster_rules), key=lambda rule: rule['version'])
        evaluations = sorted(scan(conn, cluster_evaluations), key=lambda ev: ev['created_at'])
        latest = {ev['pending_version']: ev for ev in evaluations}
        for rule in rules:
            ev = latest.get(rule['version'])
            rule['state_label'] = STATES.get(rule['state'], rule['state'])
            rule['evaluation'] = ev['code'] if ev else None
            rule['passed'] = ev['passed'] if ev else None
        return rules


@router.get('/cluster_evaluations')
def list_cluster_evaluations(user=Depends(actor)):
    def summarize(entry):
        if 'old_same' not in entry:
            return entry['load_grade'] + '：' + '、'.join(entry['reasons'])
        return (f"{entry['load_grade']}：同簇 {entry['old_same']}/{entry['cards']} → "
                f"{entry['new_same']}/{entry['cards']}")
    with transaction() as conn:
        rows = sorted(scan(conn, cluster_evaluations), key=lambda ev: ev['created_at'])
        for row in rows:
            purposes = row['detail'].get('purposes', [])
            row['summary'] = '；'.join(summarize(entry) for entry in purposes)
            row['result'] = '通过' if row['passed'] else '未通过'
        return rows


@router.post('/cluster_rules/propose')
def propose(data: ProposeRule, user=Depends(actor)):
    allow(user, ('reviewer',))
    with transaction() as conn:
        output = service.propose(conn, user, data)
        record(conn, user, 'cluster_rules.propose')
        return output


@router.post('/cluster_rules/evaluate')
def evaluate(data: EvaluateRule, user=Depends(actor)):
    allow(user, ('reviewer',))
    with transaction() as conn:
        output = service.evaluate(conn, user, data)
        record(conn, user, 'cluster_rules.evaluate')
        return output


@router.post('/cluster_rules/publish')
def publish(data: PublishRule, user=Depends(actor)):
    allow(user, ('reviewer',))
    with transaction() as conn:
        output = service.publish(conn, user, data)
        record(conn, user, 'cluster_rules.publish')
        return output
