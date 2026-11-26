        import {workspace} from '../workspace.js';
        import {el} from '../dom.js';

        const page = {
  "title": "孔形分簇门槛",
  "module": "分簇规则发布",
  "caption": "孔形分簇门槛",
  "detail": "复核员提出待发布门槛，选取已签货架卡做盲测；卡上的垛不参与拟合，新旧门槛用同一批训练垛比较。每种用途的同簇占比都不低于旧版才可发布。",
  "path": "/cluster_rules",
  "columns": [
    {
      "name": "code",
      "label": "规则号"
    },
    {
      "name": "version",
      "label": "版本"
    },
    {
      "name": "threshold",
      "label": "距离门槛"
    },
    {
      "name": "state_label",
      "label": "状态"
    },
    {
      "name": "evaluation",
      "label": "盲测记录"
    },
    {
      "name": "created_by",
      "label": "提出人"
    }
  ],
  "layout": "flip",
  "view": "grid",
  "actions": [
    {
      "name": "propose",
      "label": "提出待发布门槛",
      "path": "/cluster_rules/propose",
      "fields": [
        {
          "name": "threshold",
          "label": "距离门槛",
          "kind": "float",
          "initial": 0.3
        }
      ],
      "help": "门槛变化后原盲测记录作废，须重新盲测。",
      "roles": [
        "reviewer"
      ],
      "success": "已提出"
    },
    {
      "name": "evaluate",
      "label": "已签货架卡盲测",
      "path": "/cluster_rules/evaluate",
      "fields": [
        {
          "name": "cards",
          "label": "货架卡号",
          "kind": "json",
          "initial": [
            "PACK-0",
            "PACK-1"
          ]
        }
      ],
      "help": "只选已签发的货架卡；卡上的两个砖垛不参与拟合。",
      "roles": [
        "reviewer"
      ],
      "remember": "evaluation",
      "success": "已盲测"
    },
    {
      "name": "publish",
      "label": "发布通过的门槛",
      "path": "/cluster_rules/publish",
      "fields": [
        {
          "name": "evaluation",
          "label": "盲测记录",
          "kind": "slot",
          "initial": ""
        }
      ],
      "help": "发布失败保留旧版；发布成功后新接的试配使用新版。",
      "roles": [
        "reviewer"
      ],
      "success": "已发布"
    }
  ]
};

        export const {title} = page;
        export const key = "cluster_rules";
        export async function render(root, role) {
          await workspace(root, role, page);

        }
