import { Menu, UploadCloud } from 'lucide-react';

const Navbar = ({ onMenuClick, setActiveTab }) => {
  return (
    <header className="flex items-center justify-between px-4 md:px-8 h-15 bg-white/80 backdrop-blur-md sticky top-0 z-20 w-full">
      <div className="flex items-center gap-4">
        <button onClick={onMenuClick} className="md:hidden p-2 hover:bg-zinc-100 rounded-lg">
          <Menu size={20} />
        </button>
        <h1 className="font-semibold text-zinc-900 text-lg md:text-xl truncate">Personal Assistant</h1>
      </div>
      
      <button 
        onClick={() => setActiveTab('upload')}
        className="flex items-center gap-2 px-3 py-1.5 md:px-4 md:py-2 cursor-pointer text-zinc-700 hover:bg-zinc-50 rounded-full transition-all text-sm md:text-lg font-semibold active:scale-95"
      >
        <UploadCloud size={18} />
        <span className="hidden sm:inline">Upload</span>
      </button>
    </header>
  );
};

export default Navbar;