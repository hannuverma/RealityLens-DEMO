import heroImage from "../assets/hero.jpg";

const HeroSection = () => {
	return (
		<section className='relative overflow-hidden pt-16 md:pt-24'>
			<div className='mx-auto flex w-full max-w-5xl flex-col items-center px-5 text-center md:px-8'>
				<span className='rounded-full border border-cyan-300/30 bg-cyan-400/10 px-4 py-1 text-[11px] font-medium uppercase tracking-[0.2em] text-cyan-200'>
					The Celestial Interface
				</span>

				<h1 className='mt-6 text-4xl font-bold leading-tight text-slate-100 sm:text-5xl md:text-8xl'>
					Your AI-Powered
					<span className='block bg-linear-to-r from-indigo-300 via-violet-300 to-cyan-300 bg-clip-text text-transparent'>
						Visual Truth Layer
					</span>
				</h1>

				<p className='mt-5 max-w-2xl text-sm leading-relaxed text-slate-300 md:text-base'>
					Instantly verify screenshots, deepfakes, and manipulated stats
					with RealityLens. A native Windows tool designed for the era of
					misinformation.
				</p>

				<div className='mt-9 flex flex-col items-center gap-3 sm:flex-row'>
					<button className='w-full rounded-full border border-indigo-300/60 bg-indigo-300 px-6 py-3 text-sm font-semibold text-indigo-950 transition hover:bg-indigo-200 sm:w-auto cursor-pointer'>
						<a
							href='https://github.com/hannuverma/RealityLens-DEMO/releases/download/V4/RealityLens.exe'
							download
						>
							Download for Windows
						</a>
					</button>
					<button className='w-full rounded-full border border-slate-500/70 bg-slate-900/80 px-6 py-3 text-sm font-semibold text-slate-100 transition hover:border-slate-400 sm:w-auto cursor-pointer'>
						<a
							href='https://github.com/hannuverma/RealityLens-DEMO/releases/download/mac_version/RealityLens'
							download
						>
							Download for MacOS
						</a>
					</button>
				</div>
			</div>

			<div className='mx-auto mt-14 w-full max-w-5xl px-5 md:px-8'>
				<div className='rounded-2xl border border-slate-700/70 bg-linear-to-br from-slate-800 to-slate-900 p-3 shadow-[0_25px_90px_rgba(38,99,235,0.25)]'>
					<img
						src={heroImage}
						alt='RealityLens desktop interface'
						className='w-full rounded-xl border border-slate-700/80 object-cover'
					/>
				</div>
			</div>
		</section>
	);
};

export default HeroSection;
