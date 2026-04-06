const navItems = ["Features", "How It Works", "Demo", "Tech"];

const Navbar = () => {
	return (
		<header className='sticky top-0 z-40 border-b border-slate-800/60 bg-[#02091f]/85 backdrop-blur'>
			<nav className='mx-auto flex w-full max-w-6xl items-center justify-between px-5 py-4 md:px-8'>
				<a
					href='#'
					className='text-2xl font-semibold tracking-wide text-slate-100'
				>
					RealityLens
				</a>

				<ul className='hidden items-center gap-7 text-base font-medium text-slate-300 md:flex'>
					{navItems.map((item) => (
						<li key={item}>
							<a
								href={`#${item.toLowerCase().replaceAll(" ", "-")}`}
								className='transition-colors hover:text-white'
							>
								{item}
							</a>
						</li>
					))}
				</ul>

				<button className='rounded-full border border-indigo-300/70 bg-indigo-300/85 px-5 py-2.5 text-sm font-semibold text-indigo-950 transition hover:bg-indigo-200'>
					Get Started
				</button>
			</nav>
		</header>
	);
};

export default Navbar;
