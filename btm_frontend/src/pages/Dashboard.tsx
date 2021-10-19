import React, { useState } from 'react';

import Header from '../partials/Header';
import DashboardCard10 from '../partials/dashboard/DashboardCard10';
import Banner from '../partials/Banner';

import Warrant from '../warrant/WarrantContext';

function Dashboard() {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <Warrant>
      <div className="flex h-screen overflow-hidden">

        {/* Content area */}
        <div className="relative flex flex-col flex-1 overflow-y-auto overflow-x-hidden">

          {/*  Site header */}
          <Header sidebarOpen={sidebarOpen} setSidebarOpen={setSidebarOpen} />

          <main>
            <div className="px-4 sm:px-6 lg:px-8 py-8 w-full max-w-9xl mx-auto">

              {/* Dashboard actions */}
              <div className="sm:flex sm:justify-between sm:items-center mb-8">

                <div className="grid grid-flow-col sm:auto-cols-max justify-start sm:justify-end gap-2">
                </div>

              </div>

              {/* Cards */}
              <div className="grid grid-cols-12 gap-6">
                <DashboardCard10 />
              </div>

            </div>
          </main>

          <Banner />

        </div>
      </div>
    </Warrant>
  );
}

export default Dashboard;