import { RiKeyboardFill, RiQrScanLine, RiUserSettingsLine } from "@remixicon/react";

const steps = [
	{
		id: "01",
		title: "Press Ctrl+Shift+L",
		detail: "Global hotkey trigger works anywhere in Windows, instantly.",
		iconLabel: "Keyboard",
		icon: <RiKeyboardFill color='rgba(0,110,224,1)' />,
	},
	{
		id: "02",
		title: "Select screen area",
		detail:
			"Capture exactly what you want to verify with our pixel-perfect box.",
		iconLabel: "Scan",
		icon: <RiQrScanLine color='rgba(0,180,224,1)' />,
	},
	{
		id: "03",
		title: "Get instant AI verdict",
		detail: "Our multimodal model provides real-time forensic analysis.",
		iconLabel: "Settings",
		icon: <RiUserSettingsLine color='rgba(144,0,80,1)' type=""/>,
	},
];

const FeatureSteps = () => {
	return (
		<section
			id='how-it-works'
			className='mx-auto mt-20 w-full max-w-[85vw] px-5 md:px-8'
		>
			<div className='text-center'>
				<h2 className='text-5xl font-semibold text-slate-100'>
					Seamless Verification
				</h2>
				<p className='mt-2 text-md text-slate-400'>
					Three steps to visual certainty.
				</p>
			</div>

			<div className='mt-12 grid gap-4 md:grid-cols-3'>
				{steps.map((step) => (
					<article
						key={step.id}
						className='rounded-2xl border border-slate-800 bg-[#081535]/65 px-6 py-10 text-center shadow-[0_14px_35px_rgba(2,10,35,0.55)]'
					>
						<div className='mx-auto flex h-10 w-10 items-center justify-center rounded-xl border border-indigo-300/25 bg-indigo-300/15 text-[11px] font-semibold text-indigo-200'>
							{step.icon}
						</div>
						<h3 className='mt-4 text-lg font-medium text-white'>
							{step.title}
						</h3>
						<p className='mt-2 text-sm leading-relaxed text-slate-300'>
							{step.detail}
						</p>
					</article>
				))}
			</div>
		</section>
	);
};

export default FeatureSteps;
