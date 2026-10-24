"""DeepSeek is a bounded editor, not an agent; invalid drafts stop the build."""
import importlib.util
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch, Mock

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('dev_ai', ROOT / 'scripts/dev-ai.py')
ai = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ai)


def data():
    return {'evidence': [{'id': 'change-1', 'text': '关键词对齐变化'}],
            'examples': [{'id': 'example-1', 'code': [r'\hitsetup{keywords-hanging=true}']}],
            'comparisons': [{'id': 'keywords'}]}


def draft():
    return {'summary': '关键词续行现在默认顶格。', 'message': '旧论文需要保持原样时开启悬挂。',
            'sections': [{'title': '关键词对齐', 'description': '默认续行方式有变化。',
                'impact': '多行关键词。', 'migration': '开启悬挂可保持原样。',
                'evidence_ids': ['change-1'], 'example_ids': ['example-1'], 'comparison_ids': ['keywords']}]}


class DevAIEditorTests(unittest.TestCase):
    def test_schema_rejects_commands_unknown_evidence_and_external_content(self):
        ai.validate(draft(), data())
        invalid = []
        value = draft(); value['commands'] = ['git push']; invalid.append(value)
        value = draft(); value['sections'][0]['evidence_ids'] = ['made-up']; invalid.append(value)
        value = draft(); value['sections'][0]['example_ids'] = ['compile-my-tex']; invalid.append(value)
        value = draft(); value['sections'][0]['comparison_ids'] = ['/etc/passwd']; invalid.append(value)
        value = draft(); value['sections'][0]['description'] = 'https://example.com'; invalid.append(value)
        value = draft(); value['sections'][0]['migration'] = '在 hitsetup 中设置 design=true'; invalid.append(value)
        for value in invalid:
            with self.subTest(value=value), self.assertRaises(ValueError):
                ai.validate(value, data())

    def test_one_fixed_official_request_without_tools_or_secret_in_payload(self):
        result = {'choices': [{'finish_reason': 'stop', 'message': {'content': json.dumps(draft())}}],
                  'usage': {'total_tokens': 120}}
        opener = Mock()
        opener.open.return_value = io.BytesIO(json.dumps(result).encode())
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, {'DEV_REPORT_API_KEY': 'test-only-secret'}), \
                patch.object(ai, 'build_opener', return_value=opener):
            record = ai.generate(data(), [], Path(tmp))
            self.assertEqual(record['model'], 'deepseek-flash')
            opener.open.assert_called_once()
            request = opener.open.call_args.args[0]
            self.assertEqual(request.full_url, 'https://api.deepseek.com/chat/completions')
            payload = json.loads(request.data)
            self.assertNotIn('tools', payload)
            self.assertNotIn('test-only-secret', request.data.decode())
            self.assertEqual(payload['max_tokens'], 7000)
            self.assertEqual(payload['thinking'], {'type': 'disabled'})
            self.assertNotIn('test-only-secret', (Path(tmp) / 'DEV_AI_DRAFT.json').read_text())

    def test_missing_secret_and_tool_call_responses_are_blocked(self):
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, {'DEV_REPORT_API_KEY': ''}):
            with self.assertRaisesRegex(ValueError, 'no PDF and no publication'):
                ai.generate(data(), [], Path(tmp))
        result = {'choices': [{'finish_reason': 'stop', 'message': {'tool_calls': [{'name': 'exec'}], 'content': '{}'}}]}
        opener = Mock(); opener.open.side_effect = [io.BytesIO(json.dumps(result).encode()) for _ in range(2)]
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, {'DEV_REPORT_API_KEY': 'test-only'}), \
                patch.object(ai, 'build_opener', return_value=opener):
            with self.assertRaisesRegex(ValueError, 'tool call'):
                ai.generate(data(), [], Path(tmp))
            opener.open.assert_called_once()
            self.assertFalse((Path(tmp) / 'DEV_AI_DRAFT.json').exists())

    def test_changed_visual_comparison_cannot_be_dropped(self):
        inputs = data()
        inputs['comparisons'][0]['changed'] = True
        value = draft()
        value['sections'][0]['comparison_ids'] = []
        with self.assertRaisesRegex(ValueError, 'omitted a real changed comparison'):
            ai.validate(value, inputs)

    def test_usage_matching_normalizes_layout_but_not_names_or_values(self):
        value = draft()
        value['sections'][0]['migration'] = '使用 keywords-hanging = {true} 保留原样。'
        ai.validate(value, data())
        value['sections'][0]['migration'] = '使用 keywords-hanging=false。'
        with self.assertRaisesRegex(ValueError, 'unreviewed command/option'):
            ai.validate(value, data())

    def test_rejected_draft_is_retained_privately_and_never_becomes_public(self):
        value = draft(); value['sections'][0]['migration'] = '使用 design=true。'
        result = {'choices': [{'finish_reason': 'stop', 'message': {'content': json.dumps(value)}}]}
        opener = Mock(); opener.open.side_effect = [io.BytesIO(json.dumps(result).encode()) for _ in range(2)]
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, {'DEV_REPORT_API_KEY': 'test-only'}), \
                patch.object(ai, 'build_opener', return_value=opener):
            with self.assertRaisesRegex(ValueError, 'unreviewed command/option: design'):
                ai.generate(data(), [], Path(tmp))
            diagnostic = json.loads((Path(tmp) / 'report-build/AI_REJECTED.json').read_text())
            self.assertEqual(len(diagnostic['attempts']), 2)
            self.assertIn('design=true', diagnostic['attempts'][0]['draft_text'])
            self.assertEqual(opener.open.call_count, 2)
            self.assertFalse((Path(tmp) / 'DEV_AI_DRAFT.json').exists())
            self.assertFalse((Path(tmp) / 'DEV_UPDATE.pdf').exists())

    def test_invalid_json_can_receive_one_bounded_correction(self):
        invalid = {'choices': [{'finish_reason': 'stop', 'message': {'content': r'{"summary":"\caption"}'}}]}
        valid = {'choices': [{'finish_reason': 'stop', 'message': {'content': json.dumps(draft())}}]}
        opener = Mock(); opener.open.side_effect = [io.BytesIO(json.dumps(item).encode()) for item in (invalid, valid)]
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, {'DEV_REPORT_API_KEY': 'test-only'}), \
                patch.object(ai, 'build_opener', return_value=opener):
            record = ai.generate(data(), [], Path(tmp))
            self.assertEqual(record['calls'], 2)
            opener.open.assert_called()
            payload = json.loads(opener.open.call_args.args[0].data)
            self.assertNotIn('tools', payload)
            self.assertIn('稿件未通过检查', payload['messages'][-1]['content'])
            self.assertEqual(record['draft'], draft())
