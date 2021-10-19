import React from 'react';

function connect(url: string): void {
    let ws = new WebSocket(url); 
    ws.onopen = onOpen;
    ws.onmessage = onMessage;
    ws.onerror = onError;
    ws.onclose = onClose;
}

function onOpen(event: any): void {
    console.log("connected");
}

function onMessage(event: any): void {
    console.log(JSON.stringify(event.data));
}

function onError(event: any): void {
    console.log(JSON.stringify(event.data));
}

function onClose(event: any): void {
    console.log(JSON.stringify(event.data));
}

if (document) {
    connect('ws://localhost:8000/warrant/')
}

function WsConnection() {
    return (
        <div className="relative inline-flex ml-3">

        </div>
    );
}

export default WsConnection;