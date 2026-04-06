import { RiCodeSSlashLine, RiFlashlightFill, RiMacFill, RiSoundModuleFill } from "@remixicon/react";
const stacks = [
	{
		name: "Python",
		icon: <RiCodeSSlashLine size={32}/>,
	},
	{
		name: "PyQt6",
		icon: <RiMacFill size={32}/>,
	},
	{
		name: "Gemini AI",
		icon: <RiFlashlightFill size={32}/>,
	},
	{
		name: "Phash/CLIP",
		icon: <RiSoundModuleFill size={32}/>,
	}

];

const TechRow = () => {
	return (
		<section
			id='tech'
			className='mx-auto mt-16 w-full max-w-[85vw] px-5 md:px-8.'
		>
			<div className='rounded-2xl border border-slate-800 bg-[#07142f]/90 px-6 py-19 md:px-10'>
				<p className='text-center text-xs uppercase tracking-[0.2em] text-cyan-200/70'>
					Modular AI Architecture
				</p>
				<div className='mt-6 grid grid-cols-2 gap-3 md:grid-cols-4'>
					{stacks.map((item) => (
						<div
							key={item.name}
							className='rounded-xl border border-slate-700 bg-slate-900/40 p-4 text-center justify-center items-center flex flex-col gap-2'
						>
							{item.icon}
							<p className='mt-3 text-lg uppercase tracking-[0.09em] text-slate-200'>
								{item.name}
							</p>
						</div>
					))}
				</div>
			</div>
		</section>
	);
};

export default TechRow;
