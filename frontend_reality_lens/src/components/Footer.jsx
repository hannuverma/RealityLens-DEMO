const Footer = () => {
	return (
		<footer className='border-t border-slate-800 bg-[#030b1f]'>
			<div className='mx-auto flex w-full max-w-6xl flex-col gap-6 px-5 py-8 text-sm text-slate-400 md:flex-row md:items-center md:justify-between md:px-8'>
				<div>
					<p className='font-semibold text-slate-200'>RealityLens AI</p>
					<p className='mt-1 text-xs'>
						The desktop assistant built for visual forensics.
					</p>
				</div>

				<ul className='flex flex-wrap items-center gap-4 text-xs uppercase tracking-[0.08em] text-slate-300'>
					<li>Privacy Policy</li>
					<li>Terms of Service</li>
					<li>GitHub</li>
					<li>Twitter</li>
				</ul>

				<p className='text-xs'>
					© 2026 RealityLens AI. All rights reserved.
				</p>
			</div>
		</footer>
	);
};

export default Footer;
