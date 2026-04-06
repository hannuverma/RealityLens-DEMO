import Navbar from "./components/Navbar";
import HeroSection from "./components/HeroSection";
import FeatureSteps from "./components/FeatureSteps";
import PowerGrid from "./components/PowerGrid";
import ExperienceSection from "./components/ExperienceSection";
import TechRow from "./components/TechRow";
import CTASection from "./components/CTASection";
import Footer from "./components/Footer";

// Icon placeholders to add later (suggested set from lucide-react):
// Navbar CTA: ArrowRight
// Feature steps: Keyboard, ScanSearch, ShieldCheck
// Power cards: Zap, Sparkles, SlidersHorizontal
// Experience upload: UploadCloud
// Tech row: Cpu, LayoutGrid, Bot, Fingerprint
// Footer links (optional): Github, Twitter
const App = () => {
	return (
		<div className='min-h-screen bg-[#020817] text-slate-100'>
			<div className='pointer-events-none fixed inset-0 -z-10 bg-[radial-gradient(circle_at_20%_0%,rgba(73,106,255,0.22),transparent_34%),radial-gradient(circle_at_80%_20%,rgba(43,212,255,0.16),transparent_30%),linear-gradient(180deg,#020817_0%,#020b1f_45%,#030a1c_100%)]' />

			<Navbar />

			<main>
				<HeroSection />
				<FeatureSteps />
				<PowerGrid />
				<ExperienceSection />
				<TechRow />
				<CTASection />
			</main>

			<Footer />
		</div>
	);
};

export default App;
