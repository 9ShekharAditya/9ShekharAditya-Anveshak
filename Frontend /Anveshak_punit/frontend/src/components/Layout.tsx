import { useState } from 'react';
import { Outlet, NavLink, useLocation } from 'react-router-dom';
import {
  LayoutGrid, Globe, Orbit, FlaskConical,
  Satellite
} from 'lucide-react';
import TelescopeAdapterSource from './TelescopeAdapterSource';

const sidebarNavItems = [
  { path: '/', icon: LayoutGrid, label: 'Dashboard' },
  { path: '/candidates', icon: Globe, label: 'Exoplanet Analysis' },
  { path: '/system-3d', icon: Orbit, label: '3D System Viewer' },
  { path: '/research', icon: FlaskConical, label: 'Research', isUpcoming: true },
  { path: '/transmission-spectrum', icon: Globe, label: 'Transmission Spectrum' },
  { path: '/jwst-planning', icon: Satellite, label: 'JWST & Observatory Planning' },
];

export default function Layout() {
  const location = useLocation();
  const [selectedDataset, setSelectedDataset] = useState('confirmed');

  return (
    <div className="flex flex-col h-screen w-screen bg-bg overflow-hidden">
      {/* Top Navbar */}
      <header className="top-navbar flex items-center px-5 h-[52px] flex-shrink-0 z-30">
        <div className="flex items-center gap-8">
          {/* Logo */}
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 rounded-lg bg-gold/10 border border-gold/20 flex items-center justify-center">
              <Satellite className="w-4 h-4 text-gold" />
            </div>
            <div>
              <h1 className="text-sm font-bold text-text tracking-wide leading-none">ANVESHAK</h1>
              <p className="text-[9px] text-gold-dim italic tracking-widest">Cosmic Sleuths</p>
            </div>
          </div>
        </div>
      </header>

      {/* Main Body */}
      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar */}
        <aside className="sidebar w-[285px] flex-shrink-0 flex flex-col z-20 overflow-y-auto bg-[#07090e] border-r border-[#1a1d26]">
          {/* Navigation */}
          <nav className="px-3.5 py-2 space-y-2">
            {sidebarNavItems.map((item) => {
              const Icon = item.icon;
              const isActive = item.path === '/'
                ? location.pathname === '/'
                : location.pathname.startsWith(item.path);
              return (
                <NavLink
                  key={item.path}
                  to={item.path}
                  className={`nav-link ${isActive ? 'active' : ''}`}
                >
                  <Icon className="w-5 h-5 flex-shrink-0" />
                  <span className="text-[14px] leading-snug flex items-center gap-1.5">
                    <span>{item.label}</span>
                    {item.isUpcoming && (
                      <span className="text-[12px] font-normal text-text-muted">
                        (<span className="text-red-500 font-bold">upcoming</span>)
                      </span>
                    )}
                  </span>
                </NavLink>
              );
            })}
          </nav>

          {/* Telescope Adapter Source component */}
          <div className="mt-2">
            <TelescopeAdapterSource
              selectedDataset={selectedDataset}
              onSelectDataset={setSelectedDataset}
            />
          </div>


        </aside>

        {/* Main Content */}
        <main className="flex-1 overflow-y-auto overflow-x-hidden p-5">
          <Outlet context={{ selectedDataset, setSelectedDataset }} />
        </main>
      </div>
    </div>
  );
}
