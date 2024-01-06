'use strict';
(function() {
	document.addEventListener('readystatechange', async () => {
		if (document.readyState != 'complete') return;

		const inputsDiv   = document.querySelector('#inputs');
		const inputText   = document.querySelector('#input-text');
		const inputSubmit = document.querySelector('#input-submit');
		const inputReset  = document.querySelector('#input-reset');
		const inputStop   = document.querySelector('#input-stop');
		const msgsElement = document.querySelector('#messages-list');

		const baseUrl = (
			`${window.location.protocol}//${window.location.hostname}` +
			(window.location.port ? `:${window.location.port}`: ''));

		let genAnimElement;
		const generator = {
			isGenerating: false,
			animDotsIntSpeed: 200,
			animDotsInterval: -1,
			animDotsLength: 0,
			updateGenIntSpeed: 2000,
			updateGenInterval: -1,
		};
		generator.animDotsLength = Math.floor(generator.updateGenIntSpeed/generator.animDotsIntSpeed);
		generator.updateGenIntSpeed = generator.updateGenIntSpeed + generator.animDotsIntSpeed;

		const sendPostRequest = async (url, data=null) => {
			try {
				const requestData = {
					method: 'POST',
					headers: {'Content-Type': 'application/json'},
					body: (data == null) ? '' : JSON.stringify(data)
				};
				const response = await fetch(url, requestData);
				return await response.json();
			} catch (err) {
				return err;
			}
		};

		const addMessage = (name, text = '', date = '') => {
			const msgElement = document.createElement('p');
			msgElement.innerHTML = `<strong>${name}</strong>`;
			if (text)
				msgElement.innerHTML += text;
			if (date)
				msgElement.innerHTML += `<span>${date}</span>`;
			msgElement.setAttribute('class', 'message');
			msgsElement.appendChild(msgElement);
			return msgElement;
		};

		const addGeneratingDots = () => {
			const genText = 'Generating';
			genAnimElement = msgsElement.querySelector('#generating-msg');
			if (genAnimElement == null) {
				genAnimElement = addMessage(genText);
				genAnimElement.setAttribute('id', 'generating-msg');
			}

			let genDots = '';
			window.clearInterval(generator.animDotsInterval);
			generator.animDotsInterval = window.setInterval(() => {
				if (genDots.length < generator.animDotsLength)
					genDots += '.';
				else
					genDots = '';
				if (genAnimElement)
					genAnimElement.innerHTML = `<strong>${genText}</strong>${genDots}`;
			}, generator.animDotsIntSpeed);
		};

		const updateMessagesList = async (checkGeneration=false) => {
			const response = await sendPostRequest(`${baseUrl}/llm-list-msgs`);
			console.log(response['message']);
			// TODO: use `response['response']`
			if (checkGeneration)
				generator.isGenerating = response['is-generating'];
			if (!response['messages-list'])
				return;
			msgsElement.innerHTML = '';
			for (const msg of response['messages-list']) {
				addMessage(msg.name, msg.text.replaceAll('\n', '<br/>'), msg.date);
			}
		};

		const scrollToInputText = (smooth=false) => {
			if (smooth)
				inputsDiv.scrollIntoView({ behavior: 'smooth', block: 'end' });
			else
				inputsDiv.scrollIntoView({ block: 'end' });
			inputText.focus();
		};

		const isMouseUpLeftButton = evt => (evt.type == 'mouseup' && evt.button == 0);              // Accepts => MouseUp: Left-Button
		const isKeyUpCtrlEnter = evt => (evt.type == 'keyup' && evt.ctrlKey && evt.keyCode == 13);  // Accepts => KeyUp:   Ctrl+Enter

		const resetMessages = async () => {
			await sendPostRequest(`${baseUrl}/llm-reset-msgs`);
			generator.isGenerating = false;
			removeGeneratingCheck();
			await updateMessagesList();
		};

		const stopGenerating = async () => {
			if (!generator.isGenerating) return;
			await sendPostRequest(`${baseUrl}/llm-stop-gen`);
			generator.isGenerating = false;
			removeGeneratingCheck();
			await updateMessagesList();
		};

		const startGenerating = async () => {
			if (generator.isGenerating) return;
			const text = inputText.value.trim();
			inputText.value = '';

			if (text) {
				generator.isGenerating = true;
				await updateMessagesList();
				await startCheckGenerating();
				scrollToInputText();
				await sendPostRequest(`${baseUrl}/`, { 'prompt': text });
			}
		};

		const removeGeneratingCheck = async () => {
			window.clearInterval(generator.updateGenInterval);
			window.clearInterval(generator.animDotsInterval);
			if (genAnimElement)
				genAnimElement.remove();
		};

		const startCheckGenerating = async () => {
			await updateMessagesList();
			addGeneratingDots();
			window.clearInterval(generator.updateGenInterval);
			generator.updateGenInterval = setInterval(async () => {
				await updateMessagesList(true);
				if (generator.isGenerating) {
					addGeneratingDots();
					return;
				}
				removeGeneratingCheck();
				scrollToInputText(true);
			}, generator.updateGenIntSpeed);
		};

		inputText.value = '';
		inputText.addEventListener('keyup',     async evt => { if (isKeyUpCtrlEnter(evt))    await startGenerating(); }, false);
		inputSubmit.addEventListener('mouseup', async evt => { if (isMouseUpLeftButton(evt)) await startGenerating(); }, false);
		inputReset.addEventListener('mouseup',  async evt => { if (isMouseUpLeftButton(evt)) await resetMessages();   }, false);
		inputStop.addEventListener('mouseup',   async evt => { if (isMouseUpLeftButton(evt)) await stopGenerating();  }, false);

		await updateMessagesList(true);
		if (generator.isGenerating) {
			await startCheckGenerating();
			scrollToInputText();
		}
	});
})();
