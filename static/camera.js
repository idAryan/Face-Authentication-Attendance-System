/**
 * Shared camera capture utilities for register and attend pages.
 */
(function () {
  window.CameraHelper = {
    stream: null,

    start: function (videoEl, opts) {
      opts = opts || {};
      var facing = opts.facingMode || 'user';
      return navigator.mediaDevices
        .getUserMedia({
          video: {
            facingMode: facing,
            width: { ideal: opts.width || 640 },
            height: { ideal: opts.height || 480 },
          },
          audio: false,
        })
        .then(function (stream) {
          window.CameraHelper.stream = stream;
          if (videoEl) videoEl.srcObject = stream;
          return stream;
        })
        .catch(function (err) {
          console.error('Camera error:', err);
          throw err;
        });
    },

    stop: function () {
      if (window.CameraHelper.stream) {
        window.CameraHelper.stream.getTracks().forEach(function (t) {
          t.stop();
        });
        window.CameraHelper.stream = null;
      }
    },

    captureFrame: function (videoEl, format) {
      format = format || 'image/jpeg';
      var w = videoEl.videoWidth;
      var h = videoEl.videoHeight;
      var canvas = document.createElement('canvas');
      canvas.width = w;
      canvas.height = h;
      var ctx = canvas.getContext('2d');
      ctx.drawImage(videoEl, 0, 0, w, h);
      return canvas.toDataURL(format);
    },

    captureBlob: function (videoEl, format) {
      format = format || 'image/jpeg';
      var dataUrl = window.CameraHelper.captureFrame(videoEl, format);
      return window.CameraHelper.dataURLtoBlob(dataUrl);
    },

    dataURLtoBlob: function (dataUrl) {
      var arr = dataUrl.split(',');
      var mime = arr[0].match(/:(.*?);/)[1];
      var bstr = atob(arr[1]);
      var n = bstr.length;
      var u8 = new Uint8Array(n);
      while (n--) u8[n] = bstr.charCodeAt(n);
      return new Blob([u8], { type: mime });
    },
  };
})();
