"""Exercise the handlers emitted by the actual server-rendered UI."""
import json
import re
import subprocess

import pytest

from media_search.api.app import _ui_html


@pytest.mark.parametrize("scenario", ["success", "failed", "enqueue_error", "poll_error", "upload"])
def test_reimport_control_and_job_lifecycle(scenario):
    html = _ui_html(embedder_mode="fake", embedder_id="fake")
    assert re.search(r'<button[^>]+id="reimport"[^>]*>再取り込み</button>', html)
    assert 'aria-describedby="reimportHint"' in html
    assert "全フォルダ" in html and "既定50枚" in html
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
    if (scenario === 'enqueue_error') return {ok:false,status:409,json:async()=>({detail:'取り込み中です'})};
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
  const failed=['failed','enqueue_error','poll_error'].includes(scenario);
  assert.equal(document.getElementById('importBanner').className,failed?'import-banner err':'import-banner ok');
  if (scenario==='enqueue_error') assert.match(document.getElementById('importStatus').textContent,/409/);
  else {
    assert.equal(requests[1].url,'/api/import/jobs/job%201');
    if (scenario!=='poll_error') assert.ok(refreshes>=1,'Completion refreshes cards');
  }
})().catch(error => {console.error(error);process.exitCode=1;});
'''
    script = "const scenario=" + json.dumps(scenario) + ";\n" + harness + "\n".join(functions) + checks
    result = subprocess.run(["node", "-e", script], capture_output=True, text=True, timeout=15)
    assert result.returncode == 0, result.stderr
