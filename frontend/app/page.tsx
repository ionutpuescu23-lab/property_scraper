'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { supabase } from '@/lib/supabaseClient';

interface PropertyDeal {
  id: string;
  title?: string;
  price?: string;
  reduced?: string;
  keywords_found?: string;
  address?: string;
  postcode?: string;
  street?: string;
  image_url?: string;
  link?: string;
  portal?: string;
  source_type?: string;
  region?: string;
  area?: string;
  description?: string;
}

export default function PropertyPipelinePage() {
  const [deals, setDeals] = useState<PropertyDeal[]>([]);
  const [selectedDeal, setSelectedDeal] = useState<PropertyDeal | null>(null);
  const [unlockedDeals, setUnlockedDeals] = useState<Record<string, boolean>>({});
  const [loading, setLoading] = useState<boolean>(true);
  const [unlockFee, setUnlockFee] = useState<number>(1500);
  
  // Modal State Hooks
  const [showCheckoutModal, setShowCheckoutModal] = useState<boolean>(false);
  const [checkoutDeal, setCheckoutDeal] = useState<PropertyDeal | null>(null);
  const [showAdminPanel, setShowAdminPanel] = useState<boolean>(false);
  const [offMarketData, setOffMarketData] = useState({
    title: '',
    price: '',
    area: '',
    address: '',
    postcode: '',
    description: '',
    vendor_name: '',
    vendor_contact: '',
  });
  const [isSaving, setIsSaving] = useState(false);

  const handleAddOffMarket = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaving(true);

    const { data, error } = await supabase
      .from('property_deals')
      .insert([
        {
          ...offMarketData,
          source_type: 'direct_mail',
          reduced: 'No',
          portal: 'Direct Outreach',
          image_url: 'https://images.unsplash.com/photo-1564013799919-ab600027ffc6?auto=format&fit=crop&w=800&q=80',
          link: `off-market-${Date.now()}`,
        },
      ]);

    setIsSaving(false);
    if (error) {
      alert(`Error: ${error.message}`);
    } else {
      alert('🚀 Target saved to direct pipeline!');
      setOffMarketData({ title: '', price: '', area: '', address: '', postcode: '', description: '', vendor_name: '', vendor_contact: '' });
      setShowAdminPanel(false);
      fetchPipeline(); // This will instantly reload the dashboard list with your new deal
    }
  };

  // 1. Standalone fetch function in the main component scope
  async function fetchPipeline() {
    try {
      setLoading(true);
      const { data, error } = await supabase
        .from('property_deals')
        .select('*')
        .order('created_at', { ascending: false });

      if (error) throw error;
      if (data) setDeals(data);
    } catch (err) {
      console.error('Core Database Stream Failure:', err);
    } finally {
      setLoading(false);
    }
  }

  // 2. Lightweight hook that triggers the fetch on page load
  useEffect(() => {
    fetchPipeline();
  }, []);

  const parseScraperPrice = (priceStr?: string): number => {
    if (!priceStr) return 0;
    const digits = priceStr.replace(/[^0-9]/g, '');
    return digits ? parseInt(digits, 10) : 0;
  };

  const handleLockPackage = (uniqueKey: string, deal: PropertyDeal) => {
    if (unlockedDeals[uniqueKey]) return;
    
    setCheckoutDeal(deal);
    setShowCheckoutModal(true);
  };

  return (
    <div 
      className="min-h-screen text-slate-100 font-sans p-6 md:p-12 bg-cover bg-center bg-no-repeat bg-fixed flex flex-col justify-between"
      style={{ 
        backgroundImage: `linear-gradient(to bottom, rgba(11, 23, 27, 0.96), rgba(13, 148, 136, 0.15), rgba(2, 6, 23, 0.98)), url('https://images.unsplash.com/photo-1600585154340-be6161a56a0c?auto=format&fit=crop&w=1920&q=85')` 
      }}
    >
      <div className="w-full flex-1">
        {/* HEADER SECTION */}
        <div className="max-w-7xl mx-auto mb-8 bg-slate-900/40 border border-slate-800/60 p-6 md:p-8 rounded-2xl shadow-2xl backdrop-blur-md">
          <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-orange-500 to-amber-600 flex items-center justify-center shadow-lg shadow-orange-950/40 border border-orange-400/30 flex-shrink-0">
                <span className="text-xl font-black text-white tracking-tighter">A</span>
              </div>
              <div>
                <h1 className="text-2xl md:text-3xl font-black tracking-tight text-white flex items-center gap-2">
                  AlphaDeals <span className="text-sm font-light uppercase tracking-[0.2em] text-slate-400 bg-slate-950/80 px-2 py-0.5 rounded border border-slate-800/80 ml-1">Premium</span>
                </h1>
                <p className="text-xs md:text-sm text-slate-300 font-medium mt-1">
                  Proprietary High-Yield & Distressed Real Estate Sourcing Pipeline
                </p>
                {/* Log Off-Market Deal Toggle Button */}
                <button
                  onClick={() => setShowAdminPanel(!showAdminPanel)}
                  className={`mt-3 px-4 py-2 rounded-lg font-semibold text-sm tracking-wide shadow-md transition-all duration-200 border ${
                    showAdminPanel
                      ? 'bg-slate-800 border-slate-700 text-slate-300 hover:bg-slate-700/80'
                      : 'bg-gradient-to-r from-amber-500/20 to-orange-600/20 border-amber-500/40 text-amber-400 hover:from-amber-500/30 hover:to-orange-600/30'
                  }`}
                >
                  {showAdminPanel ? '✕ Close Form' : '➕ Log Off-Market'}
                </button>
              </div>
            </div>
            <div className="bg-slate-950/80 backdrop-blur px-4 py-2 rounded-xl border border-slate-800/80 text-xs font-mono shadow-md">
              STATUS: <span className="text-emerald-400 font-bold animate-pulse">📡 LIVE PIPELINE STREAM ACTIVE</span>
            </div>
          </div>

          {/* Dynamic Admin Input Panel Drawer */}
          {showAdminPanel && (
            <div className="max-w-7xl mx-auto mt-6 p-0.5 bg-gradient-to-br from-amber-500/30 to-orange-600/30 rounded-xl animate-in fade-in slide-in-from-top-4 duration-200">
              <div className="bg-slate-900/95 backdrop-blur-md p-6 rounded-xl border border-slate-800">
                <h3 className="text-lg font-bold text-amber-400 mb-4 flex items-center gap-2">
                  ✉️ Direct-to-Vendor Sourcing Portal
                </h3>

                <form onSubmit={handleAddOffMarket} className="space-y-4 text-slate-200">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label htmlFor="off-market-title" className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">Project Title</label>
                      <input 
                        id="off-market-title"
                        type="text" 
                        placeholder="e.g., 3 Bed Terrace Rehab"
                        value={offMarketData.title} 
                        onChange={e => setOffMarketData({...offMarketData, title: e.target.value})} 
                        className="w-full bg-slate-950/60 p-2.5 rounded-lg border border-slate-800 focus:border-amber-500/50 outline-none text-sm text-white"
                        required 
                      />
                    </div>
                    <div>
                      <label htmlFor="off-market-price" className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">Target Price</label>
                      <input 
                        id="off-market-price"
                        type="text" 
                        placeholder="e.g., £35,000"
                        value={offMarketData.price} 
                        onChange={e => setOffMarketData({...offMarketData, price: e.target.value})} 
                        className="w-full bg-slate-950/60 p-2.5 rounded-lg border border-slate-800 focus:border-amber-500/50 outline-none text-sm text-white"
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="md:col-span-2">
                      <label htmlFor="off-market-address" className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">Full Address</label>
                      <input 
                        id="off-market-address"
                        type="text" 
                        placeholder="123 Example Street"
                        value={offMarketData.address} 
                        onChange={e => setOffMarketData({...offMarketData, address: e.target.value})} 
                        className="w-full bg-slate-950/60 p-2.5 rounded-lg border border-slate-800 focus:border-amber-500/50 outline-none text-sm text-white"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">Postcode & Area</label>
                      <div className="grid grid-cols-2 gap-2">
                        <input 
                          id="off-market-postcode"
                          type="text" 
                          placeholder="L4"
                          value={offMarketData.postcode} 
                          onChange={e => setOffMarketData({...offMarketData, postcode: e.target.value})} 
                          className="w-full bg-slate-950/60 p-2.5 rounded-lg border border-slate-800 focus:border-amber-500/50 outline-none text-sm text-white"
                        />
                        <input 
                          id="off-market-area"
                          type="text" 
                          placeholder="Liverpool"
                          value={offMarketData.area} 
                          onChange={e => setOffMarketData({...offMarketData, area: e.target.value})} 
                          className="w-full bg-slate-950/60 p-2.5 rounded-lg border border-slate-800 focus:border-amber-500/50 outline-none text-sm text-white"
                          required
                        />
                      </div>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 border-t border-slate-800/60 pt-3">
                    <div>
                      <label htmlFor="off-market-vendor-name" className="block text-xs font-semibold uppercase tracking-wider text-amber-500/80 mb-1">Vendor Owner Name</label>
                      <input 
                        id="off-market-vendor-name"
                        type="text" 
                        placeholder="Vendor / Owner Full Name"
                        value={offMarketData.vendor_name} 
                        onChange={e => setOffMarketData({...offMarketData, vendor_name: e.target.value})} 
                        className="w-full bg-slate-950/60 p-2.5 rounded-lg border border-slate-800 focus:border-amber-500/50 outline-none text-sm text-white"
                      />
                    </div>
                    <div>
                      <label htmlFor="off-market-vendor-contact" className="block text-xs font-semibold uppercase tracking-wider text-amber-500/80 mb-1">Vendor Contact Info</label>
                      <input 
                        id="off-market-vendor-contact"
                        type="text" 
                        placeholder="Phone / Direct Mail Ref"
                        value={offMarketData.vendor_contact} 
                        onChange={e => setOffMarketData({...offMarketData, vendor_contact: e.target.value})} 
                        className="w-full bg-slate-950/60 p-2.5 rounded-lg border border-slate-800 focus:border-amber-500/50 outline-none text-sm text-white"
                      />
                    </div>
                  </div>

                  <div>
                    <label htmlFor="off-market-description" className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">Strategy & Condition Notes</label>
                    <textarea 
                      id="off-market-description"
                      value={offMarketData.description} 
                      onChange={e => setOffMarketData({...offMarketData, description: e.target.value})} 
                      className="w-full bg-slate-950/60 p-2.5 rounded-lg border border-slate-800 focus:border-amber-500/50 outline-none h-20 text-sm text-white resize-none"
                    />
                  </div>

                  <button 
                    type="submit" 
                    disabled={isSaving}
                    className="w-full py-2.5 mt-2 bg-gradient-to-r from-amber-500 to-orange-600 hover:from-amber-600 hover:to-orange-700 font-bold rounded-lg text-sm shadow transition duration-200 text-white"
                  >
                    {isSaving ? 'Injecting Data Pipeline...' : 'Commit Off-Market Record'}
                  </button>
                </form>

              </div>
            </div>
          )}

          {/* METRIC GRID */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6 pt-6 border-t border-slate-800/50">
            <div className="bg-slate-950/60 backdrop-blur-md p-4 rounded-xl border border-slate-800/60 shadow-lg">
              <p className="text-[10px] text-slate-400 uppercase font-bold tracking-wider">Active Sourced Assets</p>
              <p className="text-2xl font-black text-white mt-1">{loading ? '...' : deals.length}</p>
            </div>
            <div className="bg-slate-950/60 backdrop-blur-md p-4 rounded-xl border border-slate-800/60 shadow-lg">
              <p className="text-[10px] text-slate-400 uppercase font-bold tracking-wider">Price Reduced Metrics</p>
              <p className="text-2xl font-black text-amber-400 mt-1">
                {loading ? '...' : deals.filter(d => d.reduced?.toLowerCase() === 'yes').length}
              </p>
            </div>
            <div className="bg-slate-950/60 backdrop-blur-md p-4 rounded-xl border border-slate-800/60 shadow-lg">
              <p className="text-[10px] text-slate-400 uppercase font-bold tracking-wider">Target Sourcing Premium</p>
              <p className="text-2xl font-black text-emerald-400 mt-1">£{unlockFee.toLocaleString()}</p>
            </div>
          </div>
        </div>

        {/* CORE ACTIVE PIPELINE CONTAINER */}
        <div className="max-w-7xl mx-auto">
          <h3 className="text-sm font-bold text-slate-400 uppercase tracking-widest mb-4 flex items-center gap-2">📋 Active Sourced Pipelines</h3>
          
          {loading ? (
            <div className="text-center py-12 text-slate-500 font-mono text-xs">Synchronizing remote repository secure arrays...</div>
          ) : deals.length === 0 ? (
            <div className="bg-slate-900/40 border border-slate-800/80 p-8 rounded-xl text-center text-slate-400 backdrop-blur-md">
              ⚠️ Cloud connection is active, but your database is currently blank.
            </div>
          ) : (
            <div className="space-y-3">
              {deals.map((deal) => {
                const uniqueKey = deal.link || deal.id;
                const isUnlocked = unlockedDeals[uniqueKey];

                return (
                  <div 
                    key={deal.id} 
                    className="bg-slate-900/40 border border-slate-800/40 p-5 rounded-xl hover:border-slate-700/60 transition flex flex-col md:flex-row justify-between items-start md:items-center gap-4 backdrop-blur-md shadow-lg"
                  >
                    <div className="flex-1">
                      <h4 className="text-base font-extrabold text-white flex items-center gap-2">
                        🏠 {isUnlocked ? (
                          deal.title && deal.title !== "Sold House Prices" 
                            ? deal.title 
                            : (deal.street || deal.address || 'Premium Sourced Asset')
                        ) : (
                          <span className="text-teal-400 font-bold tracking-wide flex items-center gap-2">
                            AlphaDeals Premium Asset Key • <span className="text-xs text-slate-400 font-mono font-normal">[{deal.area || deal.region || 'Confidential Portfolio'}]</span>
                          </span>
                        )}
                      </h4>
                      <p className="text-xs text-slate-300 mt-1">
                        <strong>Target Signals Captured:</strong> <span className="text-rose-400 font-semibold">{deal.keywords_found || 'N/A'}</span>
                      </p>
                      <p className="text-xs font-mono text-slate-400 mt-0.5">
                        Market Value: {deal.price || '£N/A'} | Reduced Status: {deal.reduced || 'No'}
                      </p>
                    </div>

                    <div className="flex items-center gap-3 w-full md:w-auto justify-end">
                      <button
                        onClick={() => setSelectedDeal(deal)}
                        className="px-4 py-2 bg-slate-950/60 hover:bg-slate-900 text-slate-200 text-xs font-bold rounded-lg transition border border-slate-800 flex items-center gap-1.5 shadow-md"
                      >
                        🔍 Analyze Deal Structure
                      </button>
                      
                      <button
                        onClick={() => handleLockPackage(uniqueKey, deal)}
                        className={`px-4 py-2 text-xs font-black rounded-lg transition shadow-md ${
                          isUnlocked 
                            ? 'bg-emerald-950/60 border border-emerald-500/30 text-emerald-400' 
                            : 'bg-gradient-to-r from-orange-600 to-amber-600 hover:from-orange-500 hover:to-amber-500 text-white'
                        }`}
                      >
                        {isUnlocked ? '✓ Unlocked' : `🔒 Unlock for £${unlockFee}`}
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>

      {/* FOOTER AREA COMPLIANCE SECTION */}
      <footer className="max-w-7xl w-full mx-auto mt-16 pt-6 border-t border-slate-800/40 text-center text-xs text-slate-500 flex flex-col sm:flex-row justify-between items-center gap-4">
        <p>© AlphaDeals Ltd 2026. All rights reserved.</p>
        <div className="flex gap-4">
          <Link href="/privacy" className="text-slate-400 hover:text-teal-400 transition font-medium underline underline-offset-4">
            Privacy Policy
          </Link>
          <span className="text-slate-700">|</span>
          <span className="text-slate-500 font-mono">Sandbox Environment</span>
        </div>
      </footer>

      {/* ANALYSIS DRAWER OVERLAY */}
      {selectedDeal ? (() => {
        const uniqueKey = selectedDeal.link || selectedDeal.id;
        const isUnlocked = unlockedDeals[uniqueKey];
        
        const rawNumericPrice = parseScraperPrice(selectedDeal.price);
        const derivedGdv = rawNumericPrice > 0 ? Math.round(rawNumericPrice * 1.55) : 0;

        const isValidWebUrl = selectedDeal.link && (selectedDeal.link.startsWith('http://') || selectedDeal.link.startsWith('https://'));
        const isDirectMail = selectedDeal.portal?.toUpperCase() === 'DIRECT MAIL' || selectedDeal.source_type === 'direct_mail';
        const isGoogleMaps = selectedDeal.link?.includes('google.com/maps') || !isValidWebUrl;

        return (
          <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex justify-end">
            <div className="flex-1" onClick={() => setSelectedDeal(null)} />
            
            <div className="w-full max-w-[500px] bg-[#09171a] h-full border-l border-teal-950 p-8 shadow-2xl flex flex-col justify-between overflow-y-auto">
              <div>
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <span className="text-[10px] bg-amber-500/10 border border-amber-500/30 text-amber-400 font-bold px-2 py-0.5 rounded uppercase tracking-wider">
                      Asset Analysis Engine
                    </span>
                    <h2 className="text-xl font-extrabold text-white mt-2">
                      {isUnlocked ? (
                        selectedDeal.title && selectedDeal.title !== "Sold House Prices" 
                          ? selectedDeal.title 
                          : (selectedDeal.street || selectedDeal.address || 'Premium Sourced Asset')
                      ) : (
                        <span className="text-teal-400">AlphaDeals Premium Asset</span>
                      )}
                    </h2>
                    <p className="text-xs text-slate-400 mt-1">
                      {isUnlocked ? (
                        selectedDeal.address || 'Confidential Location'
                      ) : (
                        <span className="text-slate-500 italic">
                          📍 Exact address hidden until premium is claimed ({selectedDeal.area || selectedDeal.region || 'UK'})
                        </span>
                      )}
                    </p>
                  </div>
                  
                  <button onClick={() => setSelectedDeal(null)} className="p-1.5 hover:bg-slate-800 rounded-lg text-slate-400 hover:text-white transition text-sm">✕</button>
                </div>

                <div className="w-full h-64 bg-slate-900/50 rounded-lg overflow-hidden border border-slate-800/60 mb-4">
                  {selectedDeal.image_url ? (
                    <img src={selectedDeal.image_url} alt="Property Preview" className="w-full h-full object-cover" />
                  ) : (
                    <div className="w-full h-full flex flex-col items-center justify-center bg-gradient-to-b from-slate-900 to-[#16224F] text-slate-400 p-4 text-center gap-1">
                      <span>🏠</span>
                      <p className="text-xs font-semibold text-slate-300">
                        {isDirectMail ? 'Off-Market Asset Record' : 'Image Feed Standby'}
                      </p>
                    </div>
                  )}
                </div>

                <div className="space-y-4">
                  <div className="bg-slate-900/60 p-4 rounded-xl border border-slate-800/60 flex justify-between items-center">
                    <div>
                      <p className="text-xs text-slate-400 font-medium uppercase tracking-wider">Estimated Purchase Price</p>
                      <p className="text-2xl font-black text-emerald-400 mt-1">{selectedDeal.price || '£N/A'}</p>
                    </div>
                    
                    {isUnlocked ? (
                      <div className="flex flex-col gap-2">
                        {isValidWebUrl && (
                          <a href={selectedDeal.link} target="_blank" rel="noopener noreferrer" className="px-3 py-1.5 text-white text-center text-xs font-bold rounded-lg bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 transition shadow-md">
                            {isGoogleMaps ? 'View Map Location 📍' : 'Go to Portal ↗'}
                          </a>
                        )}
                        
                        {(isDirectMail || isGoogleMaps || !isValidWebUrl) && (
                          <a
                            href={`mailto:info@alphadeals.co.uk?subject=Purchase Inquiry: ${selectedDeal.title || 'Off-Market Asset'} (${selectedDeal.area || 'UK'})`}
                            className="px-3 py-1.5 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white text-xs font-black rounded-lg transition shadow-md text-center"
                          >
                            📥 Request Contract
                          </a>
                        )}
                      </div>
                    ) : (
                      <span className="text-[11px] text-slate-500 bg-slate-900/50 border border-slate-800 px-2.5 py-1 rounded-md font-medium select-none">🔗 Link Masked</span>
                    )}
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <div className="bg-slate-900/40 p-3 rounded-lg border border-slate-800/40">
                      <p className="text-[11px] text-slate-400 uppercase font-medium">Estimated Rehab Cost</p>
                      <p className="text-base font-bold text-slate-200 mt-1">£25,000</p>
                    </div>
                    <div className="bg-slate-900/40 p-3 rounded-lg border border-slate-800/40">
                      <p className="text-[11px] text-slate-400 uppercase font-medium">Target GDV</p>
                      <p className="text-base font-bold text-amber-400 mt-1">
                        {derivedGdv > 0 ? `£${derivedGdv.toLocaleString()}` : '£NaN'}
                      </p>
                    </div>
                  </div>

                  {/* SOURCING CHANNEL SIGNALS */}
                  <div className="bg-slate-900/40 p-4 rounded-xl border border-slate-800/40 space-y-2">
                    <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wide">Market Capture Signals</h4>
                    <div className="text-xs space-y-1 text-slate-400">
                      <p className="flex justify-between">
                        <span>Initial Origin Feed:</span> 
                        <span className="font-mono font-bold uppercase text-teal-400">ALPHADEALS</span>
                      </p>
                      <p className="flex justify-between">
                        <span>Sourcing Channel:</span> 
                        <span className="text-slate-200 font-mono font-semibold uppercase">
                          {isUnlocked ? (
                            selectedDeal?.source_type === 'direct_mail' ? (
                              <span className="text-amber-400 font-bold">✉️ Direct Outreach (Off-Market)</span>
                            ) : (
                              <span className="text-teal-400 font-bold">🌐 Scraped Portal Feed</span>
                            )
                          ) : (
                            <span className="text-slate-500 italic">🔒 Sourcing Route Locked</span>
                          )}
                        </span>
                      </p>
                      <p className="flex justify-between"><span>Region Scope:</span> <span className="text-slate-300 font-mono">{selectedDeal.region || 'UK'}</span></p>
                      <p className="flex justify-between"><span>Specific Area:</span> <span className="text-slate-300 font-mono">{selectedDeal.area || 'N/A'}</span></p>
                      <p className="flex justify-between"><span>Sourcing Premium:</span> <span className="text-emerald-400 font-mono font-bold">£{unlockFee}</span></p>
                    </div>
                  </div>
                </div>
              </div>

              <div className="space-y-2 mt-8">
                {!isUnlocked ? (
                  <button 
                    onClick={() => handleLockPackage(uniqueKey, selectedDeal)}
                    className="w-full py-3 bg-gradient-to-r from-orange-600 to-amber-600 hover:from-orange-500 hover:to-amber-500 text-white font-extrabold text-sm rounded-xl shadow-lg transition"
                  >
                    Lock Package & Claim Premium
                  </button>
                ) : (
                  <div className="w-full py-3 bg-emerald-900/30 border border-emerald-500/40 text-center text-emerald-400 font-bold text-xs rounded-xl">
                    ✓ Sourcing Premium Applied & Unlocked
                  </div>
                )}
                <button onClick={() => setSelectedDeal(null)} className="w-full py-2.5 bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white text-xs font-medium rounded-xl transition">
                  Return to Live Pipeline
                </button>
              </div>
            </div>
          </div>
        );
      })() : null}

      {/* PREMIUM CHECKOUT MODAL OVERLAY */}
      {showCheckoutModal && checkoutDeal && (() => {
        const uniqueKey = checkoutDeal.link || checkoutDeal.id;
        return (
          <div className="fixed inset-0 bg-black/80 backdrop-blur-md z-[100] flex items-center justify-center p-4">
            <div className="absolute inset-0" onClick={() => setShowCheckoutModal(false)} />
            <div className="relative w-full max-w-md bg-gradient-to-b from-[#0e2226] to-[#0a1118] border border-teal-500/30 rounded-2xl p-6 shadow-2xl backdrop-blur-xl animate-in fade-in zoom-in-95 duration-200">
              <div className="text-center mb-6">
                <div className="w-12 h-12 rounded-full bg-amber-500/10 border border-amber-500/30 text-amber-400 flex items-center justify-center mx-auto mb-3 text-xl">🔒</div>
                <h3 className="text-lg font-black text-white tracking-tight">Secure Premium Checkout</h3>
                <p className="text-xs text-slate-400 mt-1">AlphaDeals Proprietary Pipeline Escrow</p>
              </div>

              <div className="bg-slate-950/60 border border-slate-800/80 rounded-xl p-4 mb-6 space-y-2.5">
                <div className="flex justify-between items-start">
                  <span className="text-xs text-slate-400">Target Asset:</span>
                  <span className="text-xs text-teal-400 font-bold max-w-50 text-right truncate">
                    {checkoutDeal.title && checkoutDeal.title !== "Sold House Prices" ? checkoutDeal.title : 'Premium Sourced Asset'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-xs text-slate-400">Territory Scope:</span>
                  <span className="text-xs font-mono text-slate-300">{checkoutDeal.area || checkoutDeal.region || 'UK Scope'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-xs text-slate-400">Market Value:</span>
                  <span className="text-xs font-mono text-slate-300">{checkoutDeal.price || '£N/A'}</span>
                </div>
                <div className="border-t border-slate-800/60 pt-2.5 flex justify-between items-center">
                  <span className="text-xs font-bold text-slate-200">Sourcing Premium Fee:</span>
                  <span className="text-lg font-black text-emerald-400 font-mono">£{unlockFee.toLocaleString()}</span>
                </div>
              </div>

              <div className="space-y-2">
                <button
                  onClick={() => {
                    setUnlockedDeals(prev => ({ ...prev, [uniqueKey]: true }));
                    setShowCheckoutModal(false);
                  }}
                  className="w-full py-3 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-extrabold text-sm rounded-xl shadow-lg shadow-emerald-950/40 transition flex items-center justify-center gap-2"
                >
                  💳 Authorize Sandboxed Payment
                </button>
                <button onClick={() => setShowCheckoutModal(false)} className="w-full py-2 text-xs font-medium text-slate-500 hover:text-slate-300 transition text-center">
                  Cancel Transaction
                </button>
              </div>
            </div>
          </div>
        );
      })()}
    </div>
  );
}