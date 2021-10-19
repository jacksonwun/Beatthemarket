export interface ConnetStatus {
    connectionStatus: ConnectionStatus;
}

export enum ConnectionStatus {
    CONNECTING,
    DISCONNECTED,
    RECONNECT,
}

export type ConnectFN = () => void;