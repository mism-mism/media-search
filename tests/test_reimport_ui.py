"""Exercise the handlers emitted by the actual server-rendered UI."""
import json
import re
import subprocess

import pytest

from media_search.api.app import _ui_html


@pytest.mark.parametrize("scenario", ["success", "failed", "enqueue_error", "poll_error", "upload", "sync_success", "invalid_response"])
def test_reimport_control_and_job_lifecycle(scenario):
    html = _ui_html(embedder_mode="fake", embedder_id="fake")
    assert re.search(r'<button[^>]+id="reimport"[^>]*>再取り込み</button>', html)
    assert 'aria-describedby="reimportHint"' in html
    assert "全フォルダ" in html and "既定50枚" in html
    assert "生成に失敗した画像" in html and "上限で見送った画像" in html
    functions = []
    for name in ("setStatus", "setImportStatus", "setImportBusy", "requestJson", "runAction", "pollJob", "updateFileLabel"):
        match = re.search(r"(?:async )?function " + name + r"\(.*?\n    \}", html, re.S)
        assert match, name
        functions.append(match[0])
    for name in ("reimportBtn", "uploadBtn"):
        match = re.search(name + r"\.onclick = .*?\n    \}\);", html, re.S)
        assert match, name
        functions.append(match[0])
    harness = r'''
const assert = require('node:assert/strict');
const elements = new Map();
const document = {getElementById(id) {
  if (!elements.has(id)) elements.set(id, {disabled:false, hidden:true, textContent:'', className:''});
  return elements.get(id);
}};
const statusEl=document.getElementById('status');
const uploadBtn=document.getElementById('upload');
const reimportBtn=document.getElementById('reimport');
const uploadProduct={value:'',disabled:false};
const fileInput={files:[{name:'image.png'}],value:'image.png',disabled:false};
const currentFolder=null;
class FormData { append() {} }
let busy=false, refreshes=0, requests=[], phase=0, release;
async function refreshAssets() { refreshes++; }
const setTimeout = fn => fn();
const started = new Promise(resolve => {release=resolve;});
const fetch = async (url, options={}) => {
  requests.push({url, method: options.method || 'GET'});
  if (options.method === 'POST') {
    await started;
    if (scenario === 'enqueue_error') return {ok:false,status:409,json:async()=>({detail:{error:'import_busy',holder:'private-worker-id'}})};
    if (scenario === 'sync_success') return {ok:true,status:200,json:async()=>({imported:[],updated:['existing.png'],skipped:[]})};
    if (scenario === 'invalid_response') return {ok:true,status:200,json:async()=>({job:{job_id:'job 1'}})};
    return {ok:true,status:200,json:async()=> scenario === 'upload' ? {assets:[{}],job:{job_id:'job 1'}} : {job_id:'job 1'}};
  }
  if (scenario === 'poll_error') throw new TypeError('network unavailable');
  const status = ['queued','running',scenario === 'failed' ? 'failed' : 'succeeded'][phase++];
  return {ok:true,status:200,json:async()=>({status,processed:phase,total:3,error:status==='failed'?'実行失敗':''})};
};
'''
    checks = r'''
(async () => {
  const operation = scenario === 'upload' ? uploadBtn.onclick() : reimportBtn.onclick();
  assert.equal(busy,true);
  assert.equal(reimportBtn.disabled,true);
  assert.equal(uploadBtn.disabled,true);
  await reimportBtn.onclick();
  await uploadBtn.onclick();
  assert.equal(requests.length,1,'Repeated/overlapping clicks must not enqueue');
  assert.deepEqual(requests[0],{url:scenario==='upload'?'/api/library/upload':'/api/import',method:'POST'});
  release();
  await operation;
  assert.equal(busy,false);
  assert.equal(reimportBtn.disabled,false);
  assert.equal(uploadBtn.disabled,false);
  assert.equal(fileInput.disabled,false);
  const failed=['failed','enqueue_error','poll_error','invalid_response'].includes(scenario);
  assert.equal(document.getElementById('importBanner').className,failed?'import-banner err':'import-banner ok');
  if (scenario==='enqueue_error') {
    assert.equal(document.getElementById('importStatus').textContent,'操作に失敗しました（409）：別の取り込みが実行中です。完了後にもう一度お試しください。');
    assert.ok(!statusEl.textContent.includes('private-worker-id'));
  } else if (scenario==='sync_success') {
    assert.equal(requests.length,1,'Synchronous completion must not poll a job');
    assert.equal(refreshes,1);
    assert.match(document.getElementById('importStatus').textContent,/再取り込みが完了/);
  } else if (scenario==='invalid_response') {
    assert.equal(requests.length,1);
    assert.equal(refreshes,0);
    assert.match(document.getElementById('importStatus').textContent,/取り込みの開始結果を確認できませんでした/);
  }
  else {
    assert.equal(requests[1].url,'/api/import/jobs/job%201');
    if (scenario!=='poll_error') assert.ok(refreshes>=1,'Completion refreshes cards');
  }
})().catch(error => {console.error(error);process.exitCode=1;});
'''
    script = "const scenario=" + json.dumps(scenario) + ";\n" + harness + "\n".join(functions) + checks
    result = subprocess.run(["node", "-e", script], capture_output=True, text=True, timeout=15)
    assert result.returncode == 0, result.stderr
