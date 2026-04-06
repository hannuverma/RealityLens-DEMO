import {
	RiFlashlightFill,
	RiMacFill,
	RiSoundModuleFill,
} from "@remixicon/react";
import image from "../assets/image.png";
import image1 from "../assets/image1.png";

const PowerGrid = () => {
	return (
		<section
			id='features'
			className='mx-auto mt-20 grid w-full max-w-[85vw] gap-4 px-5 md:grid-cols-12 md:px-8'
		>
			<article className='rounded-2xl border border-slate-800 bg-[#0a1535] p-20 md:col-span-7'>
				<span className='text-xs font-medium uppercase tracking-[0.14em] text-cyan-200/85'>
					Multimodal Power
				</span>
				<h3 className='mt-3 text-3xl font-semibold leading-tight text-white'>
					Real-time analysis that
					<span className='block text-slate-200'>sees beyond pixels.</span>
				</h3>
				<p className='mt-3 max-w-xl text-sm leading-relaxed text-slate-300'>
					Our neural model analyzes lighting inconsistencies, JPEG
					artifacts, and structural geometry in milliseconds.
				</p>
				<div className='mt-6 grid grid-cols-2 gap-4'>
					<div className='rounded-xl border border-slate-700/80 bg-slate-900/50 p-4'>
						<div className='h-content rounded-lg border border-slate-700 bg-linear-to-br from-slate-800 to-slate-900'>
							<img src={image} alt='' />
						</div>
					</div>
					<div className='rounded-xl border border-slate-700/80 bg-slate-900/50 p-4'>
						<div className='h-content rounded-lg border border-slate-700 bg-linear-to-br from-slate-800 to-slate-900'>
							<img src={image1} alt='' />
						</div>
					</div>
				</div>
			</article>

			<article className='rounded-2xl border border-slate-800 bg-[#0a1535] p-20 text-center md:col-span-5 place-content-center'>
				<div className='mx-auto flex h-28 w-28 items-center justify-center rounded-full border border-cyan-300/35 bg-cyan-300/10 text-lg font-semibold text-cyan-100'>
					<RiFlashlightFill color='rgba(0,211,144,1)' size={96} />
				</div>
				<h3 className='mt-8 text-3xl font-bold text-white'>
					Fast & Lightweight
				</h3>
				<p className='mt-3 text-lg text-slate-300'>
					Under 15 MB for full AI usage. Stays out of your way until you
					need it.
				</p>
			</article>

			<article className='rounded-2xl border border-slate-800 bg-[#0a1535] p-20 md:col-span-4'>
				<div className='h-6 w-6 rounded-md '>
					<RiMacFill color='rgba(159,0,255,1)' size={32} />
				</div>
				<h3 className='mt-8 text-xl font-semibold text-white'>
					High-DPI Accuracy
				</h3>
				<p className='mt-3 text-sm text-slate-300'>
					Supports 4K UIX pipelines with sub-pixel sampling precision.
				</p>
			</article>

			<article className='rounded-2xl border border-slate-800 bg-[#0a1535] p-20 md:col-span-8 md:flex md:items-center md:justify-between'>
				<div>
					<h3 className='text-3xl font-semibold leading-tight text-white'>
						Native Windows Integration
					</h3>
					<p className='mt-3 max-w-lg text-sm text-slate-300'>
						Built specifically for Windows 10/11 using Python and PyQt5
						for a clean native desktop experience.
					</p>
					<ul className='mt-4 flex flex-wrap gap-5 text-xs uppercase tracking-[0.08em] text-slate-300'>
						<li>System Tray Accessibility</li>
						<li>Zero-Latency Capture</li>
					</ul>
				</div>

				<div className='mt-6 flex h-44 w-44 items-center justify-center rounded-full border border-slate-700 bg-slate-900/70 text-xs font-semibold text-slate-300 md:mt-0'>
					<RiSoundModuleFill color='rgba(140,0,255,1)' size={128} />
				</div>
			</article>
		</section>
	);
};

export default PowerGrid;
