import React from 'react';
import { MessageSquare, UploadCloud, Menu, X } from 'lucide-react';

const Sidebar = ({ isCollapsed, setIsCollapsed, activeTab, setActiveTab, isMobileOpen, setIsMobileOpen }) => {
  const navItems = [
    { id: 'chat', label: 'Chat', icon: MessageSquare },
    { id: 'upload', label: 'Upload', icon: UploadCloud },
  ];

  const isExpanded = !isCollapsed || isMobileOpen;

  const SidebarContent = (
    <aside className={`h-full bg-white border-r border-zinc-200/70 flex flex-col transition-all duration-300 ease-in-out ${
      isExpanded ? 'w-68' : 'w-18'
    }`}>
      {/* Header */}
      <div className={`px-6 h-20 flex items-center mb-2 ${
        isExpanded ? 'justify-between' : 'justify-center'
      }`}>
        {isExpanded && (
          <div className="flex items-center gap-3">
            {/* Logo Placeholder */}
            <div className="w-8 h-8 rounded-full bg-black/10 border border-zinc-200 shadow-sm" />
          </div>
        )}
        <button 
          onClick={() => isMobileOpen ? setIsMobileOpen(false) : setIsCollapsed(!isCollapsed)}
          className="p-1.5 hover:bg-zinc-100 rounded-full text-black transition-colors cursor-pointer"
        >
          {/* Show X only on mobile open, otherwise show Menu icon */}
          {isMobileOpen ? <X size={20} /> : <Menu size={20} />}
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 space-y-2">
        {navItems.map((item) => (
          <button
            key={item.id}
            onClick={() => {
              setActiveTab(item.id);
              if (isMobileOpen) setIsMobileOpen(false);
            }}
            className={`w-full flex items-center gap-3 transition-all cursor-pointer duration-200 ${
              isExpanded ? 'px-4 py-4' : 'justify-center px-0 py-4'
            } rounded-xl ${
              activeTab === item.id ? 'bg-gray-100 text-black' : 'text-zinc-600 hover:bg-gray-50'
            }`}
          >
            <item.icon size={20} />
            {isExpanded && <span className="font-medium text-sm">{item.label}</span>}
          </button>
        ))}
      </nav>
    </aside>
  );

  return (
    <>
      {/* Desktop Sidebar */}
      <div className="hidden md:block h-screen sticky top-0">
        {SidebarContent}
      </div>

      {/* Mobile Sidebar Overlay */}
      {isMobileOpen && (
        <div className="fixed inset-0 z-50 md:hidden">
          {/* Backdrop */}
          <div 
            className="absolute inset-0 bg-black/50 backdrop-blur-sm" 
            onClick={() => setIsMobileOpen(false)} 
          />
          
          <div className="absolute left-0 top-0 h-full w-65 animate-in slide-in-from-left duration-300">
            {SidebarContent}
          </div>
        </div>
      )}
    </>
  );
};

export default Sidebar;