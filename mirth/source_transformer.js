
var rawData = String(connectorMessage.getRawData() || '');

rawData = rawData
            .replace(/^\uFEFF/, '')         
            .replace(/\r?\n/g, '\r');        


function splitHL7(msg)  { return msg.split('\r'); }
function splitSeg(seg)  { return seg.split('|'); }
function hasCtrl(s)     { return /[\x00-\x1F\x7F]/.test(s); }
function clean(seg)     { return String(seg).replace(/[\x00-\x1F\x7F]+/g, ''); }


(function() {
    var segments = splitHL7(rawData);

    
    rawData = rawData.replace(/^[\r\n]+/, '');

    for (var i = 0; i < segments.length; i++) {
        
        var seg = segments[i].replace(/[\r\n]/g, '').trim();
        if (seg.indexOf('MSH|') === 0) {
            var fields = splitSeg(seg);
            
            var reportId = (fields.length >= 10) ? fields[9] : '';
            channelMap.put('REPORT_ID', reportId);
            logger.info('[Transformer] REPORT_ID=' + reportId);
            break;
        }
    }
})();



(function () {
    var reportLines = [];

    splitHL7(rawData).forEach(function (seg) {
        if (seg.startsWith('OBX|')) {
            var f = splitSeg(seg);
            if (f.length >= 6 && f[5].trim() !== '') {
                reportLines.push(f[5].trim());
            }
        }
    });

    
    var reportText = reportLines.join('\n');
    var reportEsc = reportText
                      .replace(/\\/g, '\\\\')
                      .replace(/\r?\n/g, '\\n')
                      .replace(/"/g, '\\"');

    channelMap.put('REPORT',     reportText);
    channelMap.put('REPORT_ESC', reportEsc);
})();


function buildJsonMessage(message) {
    var json = {}, segs = splitHL7(message);

    segs.forEach(function (seg) {
        seg = clean(seg);
        if (seg.trim() === '' || hasCtrl(seg)) return;

        var fields = splitSeg(seg);
        if (fields.length < 2) return;

        var name = seg.substring(0, 3);
        if (!json[name]) json[name] = [];

        var obj = {};
        for (var i = 1; i <= fields.length; i++) {
            obj[name + '.' + i] = fields[i - 1];
        }
        json[name].push(obj);
    });

    return json;
}


msg = JSON.stringify(buildJsonMessage(rawData));