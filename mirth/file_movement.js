var ok = $('HTTP_Backend','BACKEND_OK');

if (!ok) {
    logger.info('[Move] Backend NO OK → archivo sigue en IN');
    return '';
}

var srcDir   = $('fileDirectory');          
var fileName = $('originalFilename');       


var separator = srcDir.endsWith("\\") ? "" : "\\";    

var srcPath = srcDir + separator + fileName;


var destPath = 'C:/Users/anaso/Desktop/processed/' + fileName;



try {
    var Paths = java.nio.file.Paths;
    var Files = java.nio.file.Files;
    var src   = Paths.get(srcPath);
    var dest  = Paths.get(destPath);

    Files.createDirectories(dest.getParent());
    Files.move(src, dest, java.nio.file.StandardCopyOption.REPLACE_EXISTING);
} catch (e) {
    logger.error('[Move] No se pudo mover el archivo: ' + e);
}

return '';
