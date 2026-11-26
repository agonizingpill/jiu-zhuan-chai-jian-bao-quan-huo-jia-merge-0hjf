import hashlib
from datetime import datetime, timezone
from uuid import uuid4

import numpy as np
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from core.records import get, insert, need, scan, update
from domain import learning
from domain.brick_stacks_model import brick_stacks
from domain.cluster_rules_model import cluster_evaluations, cluster_rules
from domain.demolitions_model import demolitions
from domain.rack_candidates_model import rack_candidates
from domain.rack_merges_model import rack_merges

MIN_TRAINING = 6


def _now():
    return datetime.now(timezone.utc)


def _latest(conn, state, lock=False):
    query = select(cluster_rules).where(cluster_rules.c.state == state).order_by(cluster_rules.c.version.desc())
    if lock:
        query = query.with_for_update()
    row = conn.execute(query).mappings().first()
    return dict(row) if row else None


def _default(conn):
    top = conn.scalar(select(func.max(cluster_rules.c.version))) or 0
    row = {'code': f'RULE-{top + 1}', 'version': top + 1, 'threshold': learning.DEFAULT_THRESHOLD,
           'state': 'current', 'created_by': 'system', 'created_at': _now()}
    try:
        with conn.begin_nested():
            conn.execute(cluster_rules.insert().values(**row))
    except IntegrityError:
        return _latest(conn, 'current')
    return row


def current_rule(conn, lock=False):
    row = _latest(conn, 'current', lock)
    if row is None:
        row = _default(conn)
    return row


def ensure_default_rule():
    """启动时确保存在现用规则；已有规则则不动，兼容只做 create_all 的旧库。"""
    from core.db import transaction
    with transaction() as conn:
        current_rule(conn)


def fingerprint(current, pending):
    # 盲测结果只取决于新旧两侧门槛；任一侧数值变化都必须重测。
    return hashlib.sha256(f'current={current["threshold"]!r}|pending={pending["threshold"]!r}'.encode()).hexdigest()


def propose(conn, user, data):
    threshold = float(data.threshold)
    need(0 < threshold <= 100, '门槛须为正数且不超过 100')
    current = current_rule(conn, lock=True)
    pending = _latest(conn, 'pending', lock=True)
    if pending and pending['threshold'] == threshold:
        return pending
    need(threshold != current['threshold'], '待发布门槛须与现用门槛不同')
    if pending:
        update(conn, cluster_rules, pending['code'], state='superseded')
    top = conn.scalar(select(func.max(cluster_rules.c.version))) or 0
    return insert(conn, cluster_rules, code=f'RULE-{top + 1}', version=top + 1, threshold=threshold,
                  state='pending', created_by=user['sub'], created_at=_now())


def _inventory(conn):
    sources = {row['code']: row for row in scan(conn, demolitions)}
    allowed = {code for code, row in sources.items() if row['allowed']}
    stacks = [dict(row, load_grade=sources[row['origin']]['load_grade'])
              for row in scan(conn, brick_stacks) if row['origin'] in allowed]
    pool = [row for row in stacks if row['weighed'] and not row['merged']]
    # 已放行来源涉及的用途都算现有用途，即使暂时没有垛也要凑齐货架卡与训练垛。
    return sources, stacks, pool, {sources[code]['load_grade'] for code in allowed}


def _cards(conn, codes, sources):
    picked = []
    for code in codes:
        card = get(conn, rack_merges, code)
        candidate = get(conn, rack_candidates, card['candidate'])
        member = get(conn, brick_stacks, candidate['member'])
        pair = get(conn, brick_stacks, candidate['pair'])
        grades = {sources.get(x['origin'], {}).get('load_grade') for x in (member, pair)}
        need(len(grades) == 1 and None not in grades, f'货架卡 {code} 的两垛用途不同或来源不明')
        picked.append({'card': code, 'member': member, 'pair': pair, 'load_grade': grades.pop()})
    return picked


def _same_cluster_rate(training, cards, threshold):
    scale, clusterer = learning.model(training, threshold)
    outcomes = []
    for card in cards:
        points = np.vstack([learning.matrix([card['member']]), learning.matrix([card['pair']])])
        labels = clusterer.predict(scale.transform(points))
        outcomes.append({'card': card['card'], 'same_cluster': bool(labels[0] == labels[1])})
    same = sum(x['same_cluster'] for x in outcomes)
    return {'same': same, 'total': len(outcomes), 'rate': same / len(outcomes), 'cards': outcomes}


def evaluate(conn, user, data):
    current = current_rule(conn, lock=True)
    pending = _latest(conn, 'pending', lock=True)
    need(pending is not None, '请先提出待发布门槛')
    codes = list(dict.fromkeys(data.cards))
    need(len(codes) <= 500, '一次最多选取五百张货架卡')
    need(codes, '至少选择一张已签货架卡')
    sources, stacks, pool, purposes = _inventory(conn)
    cards = _cards(conn, codes, sources)
    excluded = {c['member']['code'] for c in cards} | {c['pair']['code'] for c in cards}
    purposes |= {c['load_grade'] for c in cards}
    passed = True
    report = []
    for grade in sorted(purposes):
        grade_cards = [c for c in cards if c['load_grade'] == grade]
        training = [s for s in pool if s['load_grade'] == grade and s['code'] not in excluded]
        entry = {'load_grade': grade, 'cards': len(grade_cards), 'training': len(training), 'reasons': []}
        if not grade_cards:
            entry['reasons'].append('该用途缺少已签货架卡')
            passed = False
        if len(training) < MIN_TRAINING:
            entry['reasons'].append(f'训练垛不足六个（{len(training)}）')
            passed = False
        if grade_cards and training:
            old = _same_cluster_rate(training, grade_cards, current['threshold'])
            new = _same_cluster_rate(training, grade_cards, pending['threshold'])
            entry.update(old_rate=old['rate'], new_rate=new['rate'], old_same=old['same'], new_same=new['same'],
                         points=[{'card': o['card'], 'old': o['same_cluster'], 'new': n['same_cluster']}
                                 for o, n in zip(old['cards'], new['cards'])])
            if new['rate'] < old['rate'] - 1e-9:
                entry['reasons'].append('同簇货架卡占比低于旧版')
                passed = False
        report.append(entry)
    row = insert(conn, cluster_evaluations, code=f'EVAL-{uuid4().hex[:12]}',
                 current_version=current['version'], current_threshold=current['threshold'],
                 pending_version=pending['version'], pending_threshold=pending['threshold'],
                 selection=codes, fingerprint=fingerprint(current, pending), passed=passed,
                 detail={'purposes': report}, created_by=user['sub'], created_at=_now())
    return dict(row, status='盲测通过' if passed else '盲测未通过')


def publish(conn, user, data):
    evaluation = get(conn, cluster_evaluations, data.evaluation, lock=True)
    current = current_rule(conn, lock=True)
    pending = _latest(conn, 'pending', lock=True)
    need(pending is not None, '没有待发布门槛')
    need(evaluation['passed'], '盲测未通过，不能发布')
    need(evaluation['fingerprint'] == fingerprint(current, pending), '现用或待发布门槛已变更，请重新盲测')
    update(conn, cluster_rules, pending['code'], state='current')
    update(conn, cluster_rules, current['code'], state='retired')
    return {'code': pending['code'], 'version': pending['version'], 'threshold': pending['threshold'],
            'status': '已发布'}
