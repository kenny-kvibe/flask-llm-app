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
			updateGenIntSpeed: 200,
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

		window.copyMessageText = evt => {
			console.log('copy....', evt);
		};

		const addCopyBtnEvents = () => {
			const copyButtons = msgsElement.querySelectorAll('.select-copy-btn');
			if (copyButtons) {
				for (const copyBtn of copyButtons) {
					copyBtn.addEventListener('mouseup', evt => {
						if (!isMouseUpLeftButton(evt)) return;
						const msgElement = evt.target.parentNode.parentNode.querySelector('.text');
						const selection = window.getSelection();
						const selectRange = document.createRange();
						selection.removeAllRanges();
						selectRange.selectNodeContents(msgElement);
						selection.addRange(selectRange);
						navigator.clipboard.writeText(msgElement.innerText);
					}, false);
				}
			}
		};

		const addMessage = (name, text = '', date = '') => {
			const msgElement = document.createElement('p');
			let html = `<strong>${name}</strong>`;
			if (text)
				html += `<span class="text">${text}</span>`;
			if (date)
				html += `<span class="date"><input type="button" value="Copy" class="select-copy-btn"/>${date}</span>`;
			msgElement.innerHTML = html;
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
			if (addGenResponse && generator.isGenerating) {
				const genResponse = generator.response['gen-response'];
				if (!genResponse)
					return;
				if (genResponse.text.length > 0 && genResponse.role != msgList[msgList.length-1].role)
					addMessage(genResponse.name, genResponse.text.replaceAll('\n', '<br/>'), genResponse.date);
			}
			addCopyBtnEvents();
			generator.response = null;
		};

		const llmResetMessages = async () => {
			await sendPostRequest(`${baseUrl}/llm-reset-msgs`);
			generator.isGenerating = false;
			await llmUpdateMessagesList();
			stopCheckGenerating();
		};

		const llmStopGenerating = async () => {
			if (!generator.isGenerating) return;
			await sendPostRequest(`${baseUrl}/llm-stop-gen`);
			generator.isGenerating = false;
			await llmUpdateMessagesList();
			stopCheckGenerating(true);
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
			inputText.removeAttribute('disabled');
			scrollToInputText(true);
			if (focusInput)
				inputText.focus();
		};

		const startCheckGenerating = async () => {
			if (generator.response == null)
				await llmUpdateMessagesList();
			inputText.setAttribute('disabled', '');
			window.clearInterval(generator.updateGenInterval);
			generator.updateGenInterval = setInterval(async () => {
				if (generator.response != null)
					return;
				await llmUpdateMessagesList(true, generator.isGenerating);
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
		if (generator.isGenerating)
			await startCheckGenerating();
		else
			inputText.focus();
		scrollToInputText();
	});
})();
