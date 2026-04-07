const CTASection = () => {
	return (
		<section className='mx-auto mt-20 w-full max-w-5xl px-5 pb-20 md:px-8'>
			<div className='rounded-3xl border border-slate-800 bg-linear-to-br from-[#0a1433] via-[#0a1638] to-[#08112a] px-6 py-16 text-center shadow-[0_20px_80px_rgba(0,0,0,0.45)] md:px-10'>
				<h2 className='text-4xl font-semibold text-white'>
					Ready to see the truth?
				</h2>
				<p className='mx-auto mt-3 max-w-xl text-sm text-slate-300'>
					RealityLens v1.0 is now available for Windows. No installation
					required, just download and run.
				</p>
				<button className='mt-8 rounded-full border border-indigo-300/60 bg-indigo-300 px-8 py-3 text-sm font-semibold text-indigo-950 transition hover:bg-indigo-200 cursor-pointer'>
					<a
						href='https://github.com/hannuverma/RealityLens-DEMO/releases/download/V4/RealityLens.exe'
						download
					>
						Download v1.0 for Windows
					</a>
				</button>
				<p className='mt-4 text-xs uppercase tracking-[0.08em] text-slate-400'>
					Size 24MB • No installation required • Windows 10/11
				</p>
			</div>
		</section>
	);
};

export default CTASection;
