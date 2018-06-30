/*
 * If the API explorer supports the user's browser, run its JavaScript; otherwise, ask the user to
 * change browsers.
 */

;(function() {
  'use strict';

  var SCRIPT_PREFIX = '/static/scripts/',
      SCRIPTS = ['api-explorer/get-results', 'api-explorer/index'],
      SUPPORTED_BROWSERS = [
        {name: 'chrome', version: 61},
        {name: 'edge', version: 16},
        {name: 'firefox', version: 60},
        {name: 'opera', version: 47},
        {name: 'safari', version: 10.1},
      ],
      UNSUPPORTED_BROWSER_MESSAGE = (
        'Please use the latest version of Firefox, Safari, or Chrome to view this page.'
      ),
      browser = {},
      supportedBrowser = {},
      index = 0;

  try {
    browser = getBrowser();
  } catch (error) {
    showUnsupportedBrowserMessage();
    return;
  }

  for (index = 0; index < SUPPORTED_BROWSERS.length; index += 1) {
    supportedBrowser = SUPPORTED_BROWSERS[index];

    if (browser.name === supportedBrowser.name && browser.version >= supportedBrowser.version) {
      addApiExplorerScript();
      return;
    }
  }

  showUnsupportedBrowserMessage();

  function addApiExplorerScript() {
    var index = 0,
        scriptElement = {};

    for (index = 0; index < SCRIPTS.length; index += 1) {
      scriptElement = document.createElement('script');
      scriptElement.src = (SCRIPT_PREFIX + SCRIPTS[index] + '.js');
      scriptElement.type = 'module';
      document.body.append(scriptElement);
    }
  }

  /** Get an object in the format `{browser: 'brower name', version: 10.1}`. */
  function getBrowser() {
    var browserIsIE = false,
        browserName = '',
        specialVersionMatch = null,
        userAgentMatch = null,
        userAgentProduct = '',
        version = '',
        versionMatch = null;

    userAgentMatch = navigator.userAgent.match(
      /(opera|chrome|safari|firefox|msie|trident(?=\/))\/?\s*(\d+)/i
    );

    userAgentProduct = userAgentMatch[1];

    browserIsIE = /trident/i.test(userAgentProduct);

    if (browserIsIE) {
      versionMatch = /\brv[ :]+(\d+)/g.exec(navigator.userAgent);

      if (versionMatch) {
        version = versionMatch[1];
      }

      return {name: 'internet explorer', version: parseFloat(version)};
    } else if (userAgentProduct === 'Chrome') {
      versionMatch = navigator.userAgent.match(/\bOPR|Edge\/(\d+)/);

      if (versionMatch) {
        version = versionMatch[1];
        return {name: 'opera', version: parseFloat(version)};
      }
    }

    version = userAgentMatch[2];

    if (version) {
      browserName = userAgentProduct;
    } else {
      browserName = navigator.appName;
      version = navigator.appVersion;
    }

    specialVersionMatch = navigator.userAgent.match(/version\/(\d+)/i);

    if (specialVersionMatch) {
      version = specialVersionMatch[1];
    }

    return {name: browserName.toLowerCase(), version: parseFloat(version)};
 }

 function showUnsupportedBrowserMessage() {
   var apiExplorer = document.getElementById('api-explorer');

   apiExplorer.innerHTML = (
     '<p class="lead m-0 text-center">' + UNSUPPORTED_BROWSER_MESSAGE + '</p>'
   );
 }
}());
