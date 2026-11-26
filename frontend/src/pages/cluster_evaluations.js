        import {workspace} from '../workspace.js';
        import {el} from '../dom.js';

        const page = {
  "title": "门槛盲测记录",
  "module": "分簇规则发布",
  "caption": "门槛盲测记录",
  "detail": "每次盲测记录新旧门槛、选取的已签货架卡与逐用途同簇占比。发布时校验记录仍对应现用与待发布门槛，门槛变更后须重测。",
  "path": "/cluster_evaluations",
  "columns": [
    {
      "name": "code",
      "label": "盲测记录"
    },
    {
      "name": "current_version",
      "label": "现用版本"
    },
    {
      "name": "current_threshold",
      "label": "现用门槛"
    },
    {
      "name": "pending_version",
      "label": "待发布版本"
    },
    {
      "name": "pending_threshold",
      "label": "待发布门槛"
    },
    {
      "name": "selection",
      "label": "盲测货架卡"
    },
    {
      "name": "result",
      "label": "是否通过"
    },
    {
      "name": "summary",
      "label": "分用途结果"
    }
  ],
  "layout": "stack",
  "view": "table",
  "actions": []
};

        export const {title} = page;
        export const key = "cluster_evaluations";
        export async function render(root, role) {
          await workspace(root, role, page);

        }
