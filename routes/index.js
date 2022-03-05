var bodyParser = require('body-parser');
var express = require('express');
const { options } = require('../app');
// var encoding = require('encoding-japanese');
var router = express.Router();

/* GET home page. */
router.get('/', function (req, res, next) {
  res.render('index', {
    title: 'Express'
  });
});


var runPython = function (res, img_url, img_base64, is_sharpen_img, is_del_line, is_tate) {
  var PythonShell = require('python-shell');
  var result;

  var options = {
    pythonPath: 'Python',
    pythonOptions: ['-u'],
    scriptPath: './'
  }

  var pyshell = new PythonShell('./python/tesseract_orc_test.py', options);

  // sends a message to the Python script via stdin
  var url = img_url;
  if (is_sharpen_img == 1) {
    is_sharpen_img = true;
  } else {
    is_sharpen_img = false;
  }
  if (is_del_line == 1) {
    is_del_line = true;
  } else {
    is_del_line = false;
  }
  if (is_tate == 1) {
    is_tate = true;
  } else {
    is_tate = false;
  }
  var data = {
    url: url,
    img_base64: img_base64,
    is_sharpen_img: is_sharpen_img,
    is_del_line: is_del_line,
    is_tate: is_tate
  };
  pyshell.send(JSON.stringify(data));

  pyshell.on('message', function (message) {
    // received a message sent from the Python script (a simple "print" statement)
    console.log("結果：" + message);
    result = JSON.parse(message);
  });

  // end the input stream and allow the process to exit
  pyshell.end(function (err, code, signal) {
    if (err) throw err;
    console.log('The exit code was: ' + code);
    console.log('The exit signal was: ' + signal);
    console.log(result);
    res.json(result);
  });
}

router.use(bodyParser.json());
router.post('/runOcr', (req, res) => {
  console.log("req.body");
  runPython(res, req.body.img_url, req.body.img_base64, req.body.is_sharpen_img, req.body.is_del_line, req.body.is_tate);
});

module.exports = router;