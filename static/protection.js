// ========================================
// 🛡️ ALPHA SECURITY PROTECTION SYSTEM
// ========================================

(function () {
    'use strict';

    // ========== DISABLE RIGHT-CLICK ==========
    document.addEventListener('contextmenu', function (e) {
        e.preventDefault();
        return false;
    });

    // ========== DISABLE DEVELOPER TOOLS SHORTCUTS ==========
    document.addEventListener('keydown', function (e) {
        // F12
        if (e.keyCode === 123) {
            e.preventDefault();
            return false;
        }

        // Ctrl+Shift+I (Inspect)
        if (e.ctrlKey && e.shiftKey && e.keyCode === 73) {
            e.preventDefault();
            return false;
        }

        // Ctrl+Shift+J (Console)
        if (e.ctrlKey && e.shiftKey && e.keyCode === 74) {
            e.preventDefault();
            return false;
        }

        // Ctrl+Shift+C (Inspect Element)
        if (e.ctrlKey && e.shiftKey && e.keyCode === 67) {
            e.preventDefault();
            return false;
        }

        // Ctrl+U (View Source)
        if (e.ctrlKey && e.keyCode === 85) {
            e.preventDefault();
            return false;
        }

        // Ctrl+S (Save Page)
        if (e.ctrlKey && e.keyCode === 83) {
            e.preventDefault();
            return false;
        }

        // Ctrl+P (Print)
        if (e.ctrlKey && e.keyCode === 80) {
            e.preventDefault();
            return false;
        }
    });

    // ========== DISABLE TEXT SELECTION ==========
    document.onselectstart = function () {
        return false;
    };

    // ========== DISABLE DRAG ==========
    document.ondragstart = function () {
        return false;
    };

    // ========== DISABLE COPY/CUT/PASTE ==========
    document.addEventListener('copy', function (e) {
        e.preventDefault();
        return false;
    });

    document.addEventListener('cut', function (e) {
        e.preventDefault();
        return false;
    });

    // ========== CONSOLE WARNINGS ==========
    console.log('%c⚠️ STOP!', 'color: red; font-size: 50px; font-weight: bold;');
    console.log('%cThis is a browser feature intended for developers.', 'font-size: 20px;');
    console.log('%cIf someone told you to copy-paste something here, it is a scam.', 'font-size: 18px; color: orange;');
    console.log('%c🔒 This site is protected. Unauthorized access attempts are logged.', 'font-size: 16px; color: red;');

    // ========== DETECT DEVTOOLS OPEN ==========
    let devtoolsOpen = false;
    const threshold = 160;

    const detectDevTools = function () {
        if (window.outerWidth - window.innerWidth > threshold ||
            window.outerHeight - window.innerHeight > threshold) {
            if (!devtoolsOpen) {
                devtoolsOpen = true;
                // Optional: redirect or alert
                // window.location.href = '/';
            }
        } else {
            devtoolsOpen = false;
        }
    };

    // Check every 500ms
    setInterval(detectDevTools, 500);

    // ========== DISABLE SCREENSHOT (Experimental) ==========
    document.addEventListener('keyup', function (e) {
        // Print Screen
        if (e.key === 'PrintScreen') {
            navigator.clipboard.writeText('');
            alert('⚠️ Screenshots are disabled on this website.');
        }
    });

    // ========== BLUR DETECTION ==========
    document.addEventListener('visibilitychange', function () {
        if (document.hidden) {
            // Page is hidden (user switched tabs)
            console.log('⚠️ User left the page');
        }
    });

})();
