import { useRef, useState } from 'react';

const ExperienceSection = () => {
	const inputRef = useRef(null);
	const [isDragging, setIsDragging] = useState(false);
	const [selectedFile, setSelectedFile] = useState(null);

	const handleFile = (file) => {
		if (!file) return;
		setSelectedFile(file);
	};

	const handleInputChange = (event) => {
		handleFile(event.target.files?.[0]);
	};

	const handleDragOver = (event) => {
		event.preventDefault();
		setIsDragging(true);
	};

	const handleDragLeave = (event) => {
		event.preventDefault();
		setIsDragging(false);
	};

	const handleDrop = (event) => {
		event.preventDefault();
		setIsDragging(false);
		handleFile(event.dataTransfer.files?.[0]);
	};

	const openFilePicker = () => {
		inputRef.current?.click();
	};

	return (
		<section
			id='demo'
			className='mx-auto mt-20 w-full max-w-[85vw] px-5 md:px-8'
		>
			<div className='grid gap-6 rounded-3xl border border-slate-800 bg-black/55 p-8 md:grid-cols-2 py-20'>
				<div>
					<h2 className='text-3xl font-semibold text-white'>
						Experience Visual Truth
					</h2>
					<p className='mt-3 max-w-md text-sm text-slate-300'>
						Drag an image here to see how RealityLens analyzes visual data
						in real-time. No sign-up required.
					</p>

					<div className='mt-7 rounded-2xl border border-slate-700 bg-slate-900/80 p-5'>
						<div className='flex items-center justify-between text-xs uppercase tracking-[0.08em] text-slate-300'>
							<span>Result Status</span>
							<span className='rounded bg-red-400/20 px-2 py-1 text-red-200'>
								Suspected
							</span>
						</div>
						<div className='mt-4 flex items-end justify-between text-sm text-slate-200'>
							<p>AI Forgery Score</p>
							<p>89% Match</p>
						</div>
						<div className='mt-2 h-2 rounded-full bg-slate-700'>
							<div className='h-2 w-[89%] rounded-full bg-linear-to-r from-violet-300 to-cyan-300' />
						</div>
						<div className='mt-4 text-xs text-slate-400'>
							41 Generation Traces • High Risk
						</div>
					</div>
				</div>

				<div
					onClick={openFilePicker}
					onDragOver={handleDragOver}
					onDragLeave={handleDragLeave}
					onDrop={handleDrop}
					role='button'
					tabIndex={0}
					onKeyDown={(event) => {
						if (event.key === 'Enter' || event.key === ' ') {
							event.preventDefault();
							openFilePicker();
						}
					}}  
					className={`rounded-2xl border border-dashed p-6 text-center transition md:p-8 ${
						isDragging
							? 'border-cyan-300 bg-cyan-300/10 shadow-[0_0_0_1px_rgba(103,232,249,0.25)]'
							: 'border-slate-600 bg-[#0a1430] hover:border-slate-500 hover:bg-[#0c1738]'
					}`}
				>
					<input
						ref={inputRef}
						type='file'
						accept='image/png,image/jpeg,image/jpg,image/webp'
						className='hidden'
						onChange={handleInputChange}
					/>

					<div className='mx-auto flex h-14 w-14 items-center justify-center rounded-full border border-slate-600 bg-slate-800 text-xs font-semibold text-slate-200'>
						Drop
					</div>
					<h3 className='mt-6 text-xl font-semibold text-white'>
						Drop image or browse files
					</h3>
					<p className='mt-2 text-sm text-slate-300'>
						Supports PNG, JPG, and WEBP up to 10MB.
					</p>

					<div className='mt-6 rounded-xl border border-slate-700 bg-slate-950/40 p-4 text-left'>
						<p className='text-xs uppercase tracking-[0.08em] text-slate-400'>
							Selected File
						</p>
						{selectedFile ? (
							<div className='mt-2 space-y-1'>
								<p className='text-sm font-medium text-white'>{selectedFile.name}</p>
								<p className='text-xs text-slate-400'>
									{Math.max(1, Math.round(selectedFile.size / 1024))} KB
								</p>
							</div>
						) : (
							<p className='mt-2 text-sm text-slate-400'>
								No file selected yet. Click or drag an image here.
							</p>
						)}
					</div>
				</div>
			</div>
		</section>
	);
};

export default ExperienceSection;
