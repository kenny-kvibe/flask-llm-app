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

		const generator = {
			isGenerating: false,
			response: null,
			updateGenIntSpeed: 120,
			updateGenInterval: -1,
		};

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

		const scrollToInputText = (smooth=false) => {
			const scrollConfig = { block: 'end' };
			if (smooth)
				scrollConfig.behavior = 'smooth';
			inputsDiv.scrollIntoView(scrollConfig);
			inputText.focus();
		};

		const isMouseUpLeftButton = evt => (evt.type == 'mouseup' && evt.button == 0);              // Accepts => MouseUp: Left-Button
		const isKeyUpCtrlEnter = evt => (evt.type == 'keyup' && evt.ctrlKey && evt.keyCode == 13);  // Accepts => KeyUp:   Ctrl+Enter

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

		const llmUpdateMessagesList = async (checkGeneration=false, addGenResponse=false) => {
			generator.response = await sendPostRequest(`${baseUrl}/llm-list-msgs`);
			if (checkGeneration)
				generator.isGenerating = generator.response['is-generating'];
			const msgList = generator.response['messages-list'];
			if (!msgList) {
				generator.response = null;
				return;
			}
			msgsElement.innerHTML = '';
			for (const message of msgList) {
				addMessage(message.name, message.text.replaceAll('\n', '<br/>'), message.date);
			}
			if (addGenResponse) {
				const genResponse = generator.response['gen-response'];
				if (generator.isGenerating && genResponse && genResponse.text.length > 0)
					addMessage(genResponse.name, genResponse.text.replaceAll('\n', '<br/>'), genResponse.date);
			}
			generator.response = null;
		};

		const llmResetMessages = async () => {
			await sendPostRequest(`${baseUrl}/llm-reset-msgs`);
			generator.isGenerating = false;
			stopCheckGenerating();
		};

		const llmStopGenerating = async () => {
			if (!generator.isGenerating) return;
			await sendPostRequest(`${baseUrl}/llm-stop-gen`);
			generator.isGenerating = false;
			stopCheckGenerating();
		};

		const startGenerating = async () => {
			if (generator.isGenerating) return;
			const text = inputText.value.trim();
			inputText.value = '';
			if (text) {
				generator.isGenerating = true;
				await startCheckGenerating();
				scrollToInputText();
				await sendPostRequest(`${baseUrl}/`, { 'prompt': text });
			}
		};

		const stopCheckGenerating = async (focusInput=false) => {
			window.clearInterval(generator.updateGenInterval);
			await llmUpdateMessagesList();
			scrollToInputText(true);
			inputText.removeAttribute('disabled');
			if (focusInput)
				inputText.focus();
		};

		const startCheckGenerating = async () => {
			await llmUpdateMessagesList();
			inputText.setAttribute('disabled', '');
			window.clearInterval(generator.updateGenInterval);
			generator.updateGenInterval = setInterval(async () => {
				if (generator.response !== null)
					return;
				await llmUpdateMessagesList(true, true);
				scrollToInputText();
				if (generator.isGenerating)
					return;
				stopCheckGenerating(true);
			}, generator.updateGenIntSpeed);
		};

		inputText.value = '';
		inputText.addEventListener('keyup',     async evt => { if (isKeyUpCtrlEnter(evt))    await startGenerating(); }, false);
		inputSubmit.addEventListener('mouseup', async evt => { if (isMouseUpLeftButton(evt)) await startGenerating(); }, false);
		inputReset.addEventListener('mouseup',  async evt => { if (isMouseUpLeftButton(evt)) await llmResetMessages();   }, false);
		inputStop.addEventListener('mouseup',   async evt => { if (isMouseUpLeftButton(evt)) await llmStopGenerating();  }, false);

		await llmUpdateMessagesList(true, true);
		scrollToInputText(true);
		if (generator.isGenerating) {
			await startCheckGenerating();
		} else
			inputText.focus();
		scrollToInputText();
	});
})();
