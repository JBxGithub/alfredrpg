import { Routes, Route } from 'react-router-dom';
import { Layout, ErrorBoundary } from './components';
import Dashboard from './pages/Dashboard';
import Chains from './pages/Chains';
import Protocols from './pages/Protocols';
import Yields from './pages/Yields';
import TVL from './pages/TVL';

function App() {
  return (
    <ErrorBoundary>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/chains" element={<Chains />} />
          <Route path="/protocols" element={<Protocols />} />
          <Route path="/yields" element={<Yields />} />
          <Route path="/tvl" element={<TVL />} />
        </Routes>
      </Layout>
    </ErrorBoundary>
  );
}

export default App;