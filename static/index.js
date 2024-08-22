function provisionInfra() {
	var selectedScenario = document.getElementById("scenario").value;
	var tfRunID = document.getElementById("tfRunID").value;

	// Redirect to provisioninn page with the selected scenario as a query parameter
	window.location.href =
		"/provision_infra?scenario=" + encodeURIComponent(selectedScenario) +
		"&wf_id=" + encodeURIComponent(tfRunID);
}

function updateProgress() {
	var urlParams = new URLSearchParams(window.location.search);
	var scenario = urlParams.get("scenario");
	var tfRunID = urlParams.get("wf_id");

	fetch("/get_progress?wf_id=" + encodeURIComponent(tfRunID))
		.then(response => {
			if (response.ok) {
				return response.json();
			} else {
				// If response status is not okay, throw an error
				throw new Error(`Failed to fetch progress. Status: ${response.status}`);
			}
		})
		.then(data => {
			// Update the progress bar
			document.getElementById("error-message").innerText = "";
			document.getElementById("progress-bar").style.width = data.progress_percent + "%";

			var currentStatusElement = document.getElementById("current-status");
			if (currentStatusElement != null) {
				currentStatusElement.innerText = data.status;
			}

			if (data.plan != "") {
				// Display the Terraform plan
				document.getElementById("terraform-plan").innerText = stripAnsi(data.plan);
				document.getElementById("terraform-plan-container").style.display = "block";
			}

			if (data.status.includes("approval")) {
				// Show the appropriate container based on the scenario
				if (scenario === "human_in_the_loop_signal") {
					document.getElementById("signal-container").style.display = "block";
				} else if (scenario === "human_in_the_loop_update") {
					document.getElementById("update-container").style.display = "block";
				}
			}

			if (data.progress_percent === 100) {
				// Redirect to order confirmation with the tfRunID
				window.location.href = "/provisioned?wf_id=" + encodeURIComponent(tfRunID);
			} else {
				// Continue updating progress every second
				setTimeout(updateProgress, 1000);
			}
		})
		.catch(error => {
			// Log the detailed error message to the console
			console.error("Error fetching progress:", error.message);

			// Display the error message in the web browser
			document.getElementById("error-message").innerText = error.message;

			// Handle the error by showing a red status bar
			document.getElementById("progress-bar").style.backgroundColor = "red";
		});
}

function signal(decision) {
	// Get the tfRunID from the URL query parameters
	var urlParams = new URLSearchParams(window.location.search);
	var tfRunID = urlParams.get("wf_id");
	var reason = document.getElementById("reason").value;

	// Perform AJAX request to the server for signaling
	fetch("/signal?wf_id=" + encodeURIComponent(tfRunID), {
		method: "POST",
		headers: {
			"Content-Type": "application/json"
		},
		body: JSON.stringify({
			decision: decision,
			reason: reason
		})
	})
		.then(response => {
			if (response.ok) {
				console.log("Signal sent successfully");
			} else {
				console.error("Failed to send signal");
			}
		})
		.catch(error => {
			console.error("Error during signal:", error.message);
		});
}

function update(decision) {
	// Get the tfRunID from the URL query parameters
	var urlParams = new URLSearchParams(window.location.search);
	var tfRunID = urlParams.get("wf_id");
	var reason = document.getElementById("reason").value;

	// Perform AJAX request to the server for updating
	fetch('/update?wf_id=' + encodeURIComponent(tfRunID), {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json'
		},
		body: JSON.stringify({
			decision: decision,
			reason: reason
		})
	})
	.then(response => {
		if (response.ok) {
			return response.json();
		} else {
			console.error('Failed to send update');
			throw new Error('Failed to send update');
		}
	})
	.then(data => {
		// Get the updateResult element
		var updateResultElement = document.getElementById('update-result');

		// Update the display with the result
		updateResultElement.innerText = data.result;

		// Check if the result contains rejected and set text color
		if (data.result.includes("rejected")) {
			updateResultElement.style.color = 'red';
		} else {
			// Reset text color if not "rejected"
			updateResultElement.style.color = '';
		}
	})
	.catch(error => {
		console.error('Error during update:', error.message);
	});
}

function reloadMainPage() {
	// Redirect to the main page
	window.location.href = "/";
}

function stripAnsi(text) {
  // This regex matches ANSI escape sequences
  const ansiRegex = /\x1b\[[0-9;]*m/g;

  // Replace the ANSI escape codes with an empty string
  return text.replace(ansiRegex, '');
}
