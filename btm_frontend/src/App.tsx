import React, { useEffect } from 'react';
import {
  Switch,
  Route,
  useLocation
} from 'react-router-dom';

import './css/style.scss';
// import { focusHandling } from 'cruip-js-toolkit';
import './charts/ChartjsConfig';

// Import pages
import Dashboard from './pages/Dashboard';

function App() {

  const location = useLocation();

  useEffect(() => {
    var document : any;
    if (document){
      let allHtml: HTMLElement = document.querySelector('html')    

      allHtml.style.scrollBehavior = 'auto';
      window.scroll({ top: 0 });
      (document.querySelector('html') as HTMLInputElement).style.scrollBehavior = ''      
    }

    // focusHandling('outline');
  }, [location.pathname]); // triggered on route change

  return (
    <>
      <Switch>
        <Route exact path="/">
          <Dashboard />
        </Route>
      </Switch>
    </>
  );
}

export default App;
