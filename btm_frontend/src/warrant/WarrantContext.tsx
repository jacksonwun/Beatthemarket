import React, { createContext, useState, useEffect, useReducer } from 'react';
// import WsConnection from './websocketUtils'
import { ConnetStatus, ConnectionStatus } from './type'
import { Wrapper } from '../components/type'

export const WarrantContext = createContext <ConnetStatus>(
    {} as ConnetStatus
);

type Reducer = (state: any, action: any) => any;

export default function Warrant({ children }: Wrapper){
    const [state, dispach] = useReducer(reducer as Reducer, { count: 0 })
    useEffect(()=>{
        const ws = new WebSocket('ws://localhost:8000/warrant/')
        console.log(ws)
    })

    return (
        <WarrantContext.Provider value={{connectionStatus:ConnectionStatus.CONNECTING}}>
            {children}
        </WarrantContext.Provider >
    )
}

function reducer(state:any, action:any):any {
    return{
        ...state,

    }
}