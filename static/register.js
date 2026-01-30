(function () {
  var video = document.getElementById('camera');
  var snapshot = document.getElementById('snapshot');
  var preview = document.getElementById('preview');
  var captureBtn = document.getElementById('captureBtn');
  var submitBtn = document.getElementById('submitBtn');
  var form = document.getElementById('registerForm');
  var msgEl = document.getElementById('registerMessage');
  var userList = document.getElementById('userList');
  var noUsers = document.getElementById('noUsers');

  var capturedDataUrl = null;

  function showMessage(text, type) {
    msgEl.textContent = text;
    msgEl.className = 'message ' + (type || '');
    msgEl.classList.remove('hidden');
  }

  function hideMessage() {
    msgEl.classList.add('hidden');
  }

  function enableSubmit(enable) {
    submitBtn.disabled = !enable;
  }

  // Start camera on load
  if (video) {
    window.CameraHelper.start(video)
      .then(function () {
        captureBtn.disabled = false;
      })
      .catch(function () {
        showMessage('Could not access camera. Allow camera permission and refresh.', 'error');
      });
  }

  if (captureBtn) {
    captureBtn.addEventListener('click', function () {
      if (!video || !video.srcObject) return;
      capturedDataUrl = window.CameraHelper.captureFrame(video);
      if (snapshot) {
        var ctx = snapshot.getContext('2d');
        snapshot.width = video.videoWidth;
        snapshot.height = video.videoHeight;
        ctx.drawImage(video, 0, 0);
        snapshot.classList.remove('hidden');
        video.classList.add('hidden');
      }
      if (preview) {
        preview.innerHTML = '<img src="' + capturedDataUrl + '" alt="Captured">';
        preview.classList.remove('hidden');
      }
      enableSubmit(true);
      hideMessage();
    });
  }

  if (form) {
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      if (!capturedDataUrl) {
        showMessage('Capture a photo first.', 'error');
        return;
      }
      var user_id = (document.getElementById('user_id') && document.getElementById('user_id').value) || '';
      var name = (document.getElementById('name') && document.getElementById('name').value) || '';
      if (!user_id.trim() || !name.trim()) {
        showMessage('Enter User ID and Name.', 'error');
        return;
      }
      submitBtn.disabled = true;
      fetch('/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: user_id.trim(),
          name: name.trim(),
          image: capturedDataUrl,
        }),
      })
        .then(function (r) { return r.json(); })
        .then(function (data) {
          if (data.success) {
            showMessage(data.message, 'success');
            capturedDataUrl = null;
            if (preview) { preview.innerHTML = ''; preview.classList.add('hidden'); }
            if (snapshot) { snapshot.classList.add('hidden'); }
            if (video) { video.classList.remove('hidden'); }
            enableSubmit(false);
            addUserToList({ user_id: user_id.trim(), name: name.trim() });
          } else {
            showMessage(data.message || 'Registration failed.', 'error');
            submitBtn.disabled = false;
          }
        })
        .catch(function () {
          showMessage('Network error. Try again.', 'error');
          submitBtn.disabled = false;
        });
    });
  }

  function addUserToList(user) {
    if (!userList) return;
    noUsers && (noUsers.style.display = 'none');
    var li = document.createElement('li');
    li.setAttribute('data-user-id', user.user_id);
    li.innerHTML = user.name + ' <span class="uid">(' + user.user_id + ')</span> ' +
      '<button type="button" class="btn-small delete-user" data-user-id="' + user.user_id + '">Remove</button>';
    userList.appendChild(li);
    li.querySelector('.delete-user').addEventListener('click', function () {
      deleteUser(user.user_id, li);
    });
  }

  function deleteUser(userId, liEl) {
    fetch('/api/users/' + encodeURIComponent(userId), { method: 'DELETE' })
      .then(function (r) {
        if (r.ok && liEl && liEl.parentNode) {
          liEl.parentNode.removeChild(liEl);
          if (userList && !userList.children.length) noUsers && (noUsers.style.display = 'block');
        }
      });
  }

  if (userList) {
    userList.querySelectorAll('.delete-user').forEach(function (btn) {
      btn.addEventListener('click', function () {
        var li = btn.closest('li');
        var uid = btn.getAttribute('data-user-id');
        if (uid) deleteUser(uid, li);
      });
    });
  }

  window.addEventListener('beforeunload', function () {
    window.CameraHelper.stop();
  });
})();
