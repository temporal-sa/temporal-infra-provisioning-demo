function generateUUID() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        var r = Math.random() * 16 | 0,
            v = c == 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
}

function clearErrorMessage() {
	document.getElementById("errorMessage").innerText = "";
	document.getElementById("errorMessage").style.display = "none";
}

function showErrorMessage(message) {
	document.getElementById("errorMessage").innerText = message;
	document.getElementById("errorMessage").style.display = "block";
}

function runWorkflow() {
	var selectedScenario = document.getElementById("scenario").value;
	var ephemeralTTL = document.getElementById("ephemeralTTL").valueAsNumber;
	var deploymentPrefix = document.getElementById("deploymentPrefix").value;
	var tfRunID = "";

	if (deploymentPrefix === "") {
		showErrorMessage("Please enter a deployment prefix");
		return;
	} else {
		clearErrorMessage();
	}

	if (selectedScenario === "destroy") {
		tfRunID = `deprovision-infra-${generateUUID()}`;
	} else {
		tfRunID = `provision-infra-${generateUUID()}`;
	}

	// Redirect to provisioninn page with the selected scenario as a query parameter
	window.location.href =
		"/run_workflow?scenario=" + encodeURIComponent(selectedScenario) +
		"&wf_id=" + encodeURIComponent(tfRunID) +
		"&ephemeral_ttl=" + encodeURIComponent(ephemeralTTL) +
		"&deployment_prefix=" + encodeURIComponent(deploymentPrefix);
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
			clearErrorMessage();
			document.getElementById("progressBar").style.width = data.progress_percent + "%";

			var currentStatusElement = document.getElementById("currentStatus");
			if (currentStatusElement != null) {
				currentStatusElement.innerText = data.status;
			}

			if (scenario !== "destroy" && data.plan != "") {
				// Display the Terraform plan
				document.getElementById("terraformPlan").innerText = stripAnsi(data.plan);
				document.getElementById("terraformPlanContainer").style.display = "block";
			}

			if (data.status.includes("approval")) {
				// Show the appropriate container based on the scenario
				if (scenario === "human_in_the_loop_signal") {
					document.getElementById("signalContainer").style.display = "block";
				} else if (scenario === "human_in_the_loop_update") {
					document.getElementById("updateContainer").style.display = "block";
				}

				document.getElementById("newPlanContainer").style.display = "block";
			}

			if (data.progress_percent === 100) {
				// Redirect to provisioned confirmation with the tfRunID
				window.location.href =
					"/provisioned?wf_id=" + encodeURIComponent(tfRunID) +
					"&scenario=" + encodeURIComponent(scenario);
			} else {
				// Continue updating progress every second
				setTimeout(updateProgress, 1000);
			}
		})
		.catch(error => {
			// Log the detailed error message to the console
			console.error("Error fetching progress:", error.message);

			// Display the error message in the web browser
			showErrorMessage(error.message);
			// Handle the error by showing a red status bar
			document.getElementById("progressBar").style.backgroundColor = "red";
		});
}

function signal(signalType, payload) {
	// Get the tfRunID from the URL query parameters
	var urlParams = new URLSearchParams(window.location.search);
	var tfRunID = urlParams.get("wf_id");

	// Perform AJAX request to the server for signaling
	fetch("/signal?wf_id=" + encodeURIComponent(tfRunID), {
		method: "POST",
		headers: {
			"Content-Type": "application/json"
		},
		body: JSON.stringify({
			signalType: signalType,
			payload: payload
		})
	})
		.then(response => {
			if (response.ok) {
				console.log("Signal sent successfully");
				if (signalType == "request_continue_as_new") {
					document.getElementById("newPlanContainer").style.display = "none";
					document.getElementById("signalContainer").style.display = "none";
					document.getElementById("updateContainer").style.display = "none";
					document.getElementById("terraformPlanContainer").style.display = "none";
				}
			} else {
				console.error("Failed to send signal");
				showErrorMessage("Signal sent failed");
			}
		})
		.catch(error => {
			console.error("Error during signal:", error.message);
			showErrorMessage("Error during signal: " + error.message);
		});
}

function update(updateType, decision) {
	// Get the tfRunID from the URL query parameters
	var urlParams = new URLSearchParams(window.location.search);
	var tfRunID = urlParams.get("wf_id");
	var reason = document.getElementById("reason").value;
	clearErrorMessage();

	// Perform AJAX request to the server for updating
	fetch("/update?wf_id=" + encodeURIComponent(tfRunID), {
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
		if (response.status !== 200) {
			console.error("Failed to send update");
			updateResultElement.style.display = "block";
			updateResultElement.innerText = "Update sent failed, enter a reason and try again."
		}
	})
	.catch(error => {
		console.error("Error during update:", error.message);
	});
}

function handleScenarioChange(event) {
	var scenario = event.target.value;
	console.log(scenario);
	if (scenario === "ephemeral") {
		document.getElementById("ephemeralContainer").style.display = "block";
	} else {
		document.getElementById("ephemeralContainer").style.display = "none";
	}
}

function reloadMainPage() {
	// Redirect to the main page
	window.location.href = "/";
}

function stripAnsi(text) {
  // This regex matches ANSI escape sequences
  const ansiRegex = /\x1b\[[0-9;]*m/g;

  // Replace the ANSI escape codes with an empty string
  return text.replace(ansiRegex, "");
}
