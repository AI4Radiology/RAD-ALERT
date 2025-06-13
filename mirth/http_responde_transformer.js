var ok = msg.ack && msg.ack.toLowerCase() === 'bien recibido';

connectorMap.put('BACKEND_OK', ok);
logger.info('[HTTP_Backend-Response] ack=' + msg.ack + '  BACKEND_OK=' + ok);