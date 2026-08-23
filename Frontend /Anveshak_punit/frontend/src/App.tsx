import { Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout';
import Overview from './pages/Overview';
import CandidatesList from './pages/CandidatesList';
import CandidateDetail from './pages/CandidateDetail';
import ThreeDSystemViewer from './pages/ThreeDSystemViewer';
import TransmissionSpectrumPage from './pages/TransmissionSpectrumPage';
import JwstObservatoryPlanningPage from './pages/JwstObservatoryPlanningPage';

function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Overview />} />
        <Route path="candidates" element={<CandidatesList />} />
        <Route path="candidates/:id" element={<CandidateDetail />} />
        <Route path="system-3d" element={<ThreeDSystemViewer />} />
        <Route path="transmission-spectrum" element={<TransmissionSpectrumPage />} />
        <Route path="jwst-planning" element={<JwstObservatoryPlanningPage />} />

        {/* Aliased routes for sidebar navigation */}
        <Route path="research" element={<Overview />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}

export default App;
