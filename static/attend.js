(function () {
  var video = document.getElementById('attendCamera');
  var snapshot = document.getElementById('attendSnapshot');
  var statusEl = document.getElementById('attendStatus');
  var identifyResult = document.getElementById('identifyResult');
  var punchInBtn = document.getElementById('punchInBtn');
  var punchOutBtn = document.getElementById('punchOutBtn');
  var punchMessage = document.getElementById('punchMessage');

  function setStatus(text) {
    if (statusEl) statusEl.textContent = text;
  }

  function setIdentifyResult(text, isSuccess) {
    if (!identifyResult) return;
    identifyResult.textContent = text;
    identifyResult.className = 'identify-result ' + (isSuccess ? 'success' : '');
  }

  function showPunchMessage(text, isSuccess) {
    punchMessage.textContent = text;
    punchMessage.className = 'message ' + (isSuccess ? 'success' : 'error');
    punchMessage.classList.remove('hidden');
  }

  function sendImageToApi(endpoint) {
    if (!video || !video.srcObject) {
      showPunchMessage('Camera not ready.', false);
      return;
    }
    var dataUrl = window.CameraHelper.captureFrame(video);
    return fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ image: dataUrl }),
    })
      .then(function (r) { return r.json(); });
  }

  function doPunch(endpoint, btn) {
    btn.disabled = true;
    setIdentifyResult('Verifying face and recording…');
    sendImageToApi(endpoint)
      .then(function (data) {
        if (data.success) {
          showPunchMessage(data.message || 'Recorded.', true);
          setIdentifyResult('Identified: ' + (data.name || data.user_id), true);
        } else {
          showPunchMessage(data.message || 'Failed.', false);
          setIdentifyResult(data.message || 'No match or verification failed.', false);
        }
      })
      .catch(function () {
        showPunchMessage('Network error.', false);
        setIdentifyResult('Error.', false);
      })
      .finally(function () {
        btn.disabled = false;
      });
  }

  if (video) {
    window.CameraHelper.start(video)
      .then(function () {
        setStatus('Camera ready. Look at the camera and blink when prompted, then Punch In or Punch Out.');
        punchInBtn.disabled = false;
        punchOutBtn.disabled = false;
      })
      .catch(function () {
        setStatus('Could not access camera. Allow camera permission and refresh.');
      });
  }

  if (punchInBtn) {
    punchInBtn.addEventListener('click', function () {
      doPunch('/api/punch-in', punchInBtn);
    });
  }
  if (punchOutBtn) {
    punchOutBtn.addEventListener('click', function () {
      doPunch('/api/punch-out', punchOutBtn);
    });
  }

  window.addEventListener('beforeunload', function () {
    window.CameraHelper.stop();
  });
})();
