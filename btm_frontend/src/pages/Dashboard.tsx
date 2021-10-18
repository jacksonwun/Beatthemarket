import React, { useState, useEffect } from 'react';

import Header from '../partials/Header';
import DashboardCard10 from '../partials/dashboard/DashboardCard10';
import Banner from '../partials/Banner';

function connect(url: string): void {
      let ws = new WebSocket(url); 
      ws.onopen = onOpen;
      ws.onmessage = onMessage;
      ws.onerror = onError;
      ws.onclose = onClose;
  }
//indicates that the connection is ready to send and receive data

function onOpen(event: any): void {
    console.log("connected");
//$("#btnConnect").html("Connected");

//     btnConnect.innerHTML = "Connected";

}
//An event listener to be called when a message is received from the server

function onMessage(event: any): void {
}
//An event listener to be called when an error occurs. This is a simple event named "error".

function onError(event: any): void {
    console.log(JSON.stringify(event.data));
}
//An event listener to be called when the WebSocket connection's readyState changes to CLOSED.

function onClose(event: any): void {
    console.log(JSON.stringify(event.data));
}

if (document) {
  connect('ws://localhost:8000/warrant/')
}

function Dashboard() {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="flex h-screen overflow-hidden">

      {/* Sidebar */}
      {/* <Sidebar sidebarOpen={sidebarOpen} setSidebarOpen={setSidebarOpen} /> */}

      {/* Content area */}
      <div className="relative flex flex-col flex-1 overflow-y-auto overflow-x-hidden">

        {/*  Site header */}
        <Header sidebarOpen={sidebarOpen} setSidebarOpen={setSidebarOpen} />

        <main>
          <div className="px-4 sm:px-6 lg:px-8 py-8 w-full max-w-9xl mx-auto">

            {/* Welcome banner */}
            {/* <WelcomeBanner /> */}

            {/* Dashboard actions */}
            <div className="sm:flex sm:justify-between sm:items-center mb-8">

              {/* Left: Avatars */}
              {/* <DashboardAvatars /> */}

              {/* Right: Actions */}
              <div className="grid grid-flow-col sm:auto-cols-max justify-start sm:justify-end gap-2">
                {/* Filter button */}
                {/* <FilterButton /> */}
                {/* Datepicker built with flatpickr */}
                {/* <Datepicker /> */}
                {/* Add view button */}
                {/* <button className="btn bg-indigo-500 hover:bg-indigo-600 text-white">
                    <svg className="w-4 h-4 fill-current opacity-50 flex-shrink-0" viewBox="0 0 16 16">
                        <path d="M15 7H9V1c0-.6-.4-1-1-1S7 .4 7 1v6H1c-.6 0-1 .4-1 1s.4 1 1 1h6v6c0 .6.4 1 1 1s1-.4 1-1V9h6c.6 0 1-.4 1-1s-.4-1-1-1z" />
                    </svg>
                    <span className="hidden xs:block ml-2">Add view</span>
                </button>                 */}
              </div>

            </div>

            {/* Cards */}
            <div className="grid grid-cols-12 gap-6">

              {/* Line chart (Acme Plus) */}
              {/* <DashboardCard01 /> */}
              {/* Line chart (Acme Advanced) */}
              {/* <DashboardCard02 /> */}
              {/* Line chart (Acme Professional) */}
              {/* <DashboardCard03 /> */}
              {/* Bar chart (Direct vs Indirect) */}
              {/* <DashboardCard04 /> */}
              {/* Line chart (Real Time Value) */}
              {/* <DashboardCard05 /> */}
              {/* Doughnut chart (Top Countries) */}
              {/* <DashboardCard06 /> */}
              {/* Table (Top Channels) */}
              {/* <DashboardCard07 /> */}
              {/* Line chart (Sales Over Time) */}
              {/* <DashboardCard08 /> */}
              {/* Stacked bar chart (Sales VS Refunds) */}
              {/* <DashboardCard09 /> */}
              {/* Card (Customers) */}
              <DashboardCard10 />
              {/* Card (Reasons for Refunds) */}
              {/* <DashboardCard11 /> */}
              {/* Card (Recent Activity) */}
              {/* <DashboardCard12 /> */}
              {/* Card (Income/Expenses) */}
              {/* <DashboardCard13 /> */}
              
            </div>

          </div>
        </main>

        <Banner />

      </div>
    </div>
  );
}

export default Dashboard;